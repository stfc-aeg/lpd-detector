"""
ExcaliburFrameProducer - load EXCALIBUR frames from packet capture file and send via UDP.

Tim Nicholls, STFC Application Engineering Group.
"""

import struct
import logging
import argparse
import os
import socket
import time
import random
import dpkt

class ExcaliburFrame(object):
    """
    Container class for EXCALIBUR frame packet data
    """
    frame_count = 0
    SOF_MARKER = 1 << 31
    EOF_MARKER = 1 << 30
    NUM_SUBFRAMES = 2

    def __init__(self, frame_num):

        ExcaliburFrame.frame_count += 1

        self.frame_num = frame_num
        self.trailer_frame_num = None
        self.packets = []
        self.sofs = []
        self.eofs = []

    def append_packet(self, packet):
        """Append packet to frame packet list."""
        self.packets.append(packet)

    def add_sof(self, subframe):
        """Add subframe SOF marker to list."""
        self.sofs.append(subframe)

    def add_eof(self, subframe):
        """Add subframe EOF marker to list."""
        self.eofs.append(subframe)

    def set_trailer_frame_num(self, frame_num):
        """Set the trailer frame number in the frame."""

        # If trailer frame number is already set, e.g. for earlier subframes, check it matches
        if self.trailer_frame_num is not None:
            if frame_num != self.trailer_frame_num:
                logging.warning(
                    "Mismatched trailer frame numbers on frame %d: %d/%d",
                    self.frame_num, self.trailer_frame_num, frame_num
                )
        self.trailer_frame_num = frame_num

    def num_packets(self):
        """Return the number of packets in the frame."""
        return len(self.packets)

    def frame_size(self):
        """Return the size of the packet data in the frame."""
        return sum([len(packet) for packet in self.packets])

    def num_sofs_seen(self):
        """Return the number of SOF markers seen."""
        return len(self.sofs)

    def num_eofs_seen(self):
        """Returm the number of EOF markers seen."""
        return len(self.eofs)


class ExcaliburFrameProducerDefaults(object):
    """
    Holds default values for frame producer parameters.
    """

    def __init__(self):

        self.ip_addr = 'localhost'
        self.port = 61649
        self.num_frames = 0
        self.tx_interval = 0
        self.drop_frac = 0
        self.drop_list = None

        self.log_level = 'info'
        self.log_levels = {
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'info': logging.INFO,
            'debug': logging.DEBUG,
        }

        self.pcap_file = 'excalibur.pcap'


class Range(argparse.Action):
    """
    Range validating action for argument parser.
    """
    def __init__(self, min=None, max=None, *args, **kwargs):
        self.min = min
        self.max = max
        kwargs["metavar"] = "[%d-%d]" % (self.min, self.max)
        super(Range, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        if not self.min <= value <= self.max:
            msg = 'invalid choice: %r (choose from [%d-%d])' % \
                (value, self.min, self.max)
            raise argparse.ArgumentError(self, msg)
        setattr(namespace, self.dest, value)


class ExcaliburFrameProducer(object):
    """
    EXCALIBUR frame procducer - loads frame packets data from capture file and replays it to
    a receiver via a UDP socket.
    """

    def __init__(self):
        """
        Initialise the frame producer object, setting defaults and parsing command-line options.
        """

        # Create an empty list for frame storage
        self.frames = []

        # Load default parameters
        self.defaults = ExcaliburFrameProducerDefaults()

        # Set the terminal width for argument help formatting
        try:
            term_columns = int(os.environ['COLUMNS']) - 2
        except (KeyError, ValueError):
            term_columns = 100

        # Build options for the argument parser
        parser = argparse.ArgumentParser(
            prog='excalibur_frame_producer.py', description='EXCALIBUR frame producer',
            formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(
                prog, max_help_position=40, width=term_columns)
        )

        parser.add_argument(
            'pcap_file', type=argparse.FileType('rb'),
            default=self.defaults.pcap_file,
            help='Packet capture file to load'
        )

        parser.add_argument(
            '--address', '-a', type=str, dest='ip_addr',
            default=self.defaults.ip_addr, metavar='ADDR',
            help='Hostname or IP address to transmit UDP frame data to'
        )
        parser.add_argument(
            '--port', '-p', type=int, dest='port',
            default=self.defaults.port, metavar='PORT',
            help='Port number to transmit UDP frame data to'
        )
        parser.add_argument(
            '--frames', '-n', type=int, dest='num_frames',
            default=self.defaults.num_frames, metavar='FRAMES',
            help='Number of frames to transmit (0 = send all frames found in packet capture file'
        )
        parser.add_argument(
            '--interval', '-i', type=float, dest='tx_interval',
            default=self.defaults.tx_interval, metavar='INTERVAL',
            help='Interval in seconds between transmission of frames'
        )
        parser.add_argument(
            '--drop_frac', type=float, dest='drop_frac',
            min=0.0, max=1.0, action=Range,
            default=self.defaults.drop_frac, metavar='FRACTION',
            help='Fraction of packets to drop')
        parser.add_argument(
            '--drop_list', type=int, nargs='+', dest='drop_list',
            default=self.defaults.drop_list,
            help='Packet number(s) to drop from each frame',
        )
        parser.add_argument(
            '--logging', type=str, dest='log_level',
            default=self.defaults.log_level, choices=self.defaults.log_levels.keys(),
            help='Set logging output level'
        )

        # Parse arguments
        self.args = parser.parse_args()

        # Map logging level option onto real level
        if self.args.log_level in self.defaults.log_levels:
            log_level = self.defaults.log_levels[self.args.log_level]
        else:
            log_level = self.defaults.log_levels[self.defaults.log_level]

        # Set up logging
        logging.basicConfig(
            level=log_level, format='%(levelname)1.1s %(message)s',
            datefmt='%y%m%d %H:%M:%S'
        )

        # Initialise the packet capture file reader
        self.pcap = dpkt.pcap.Reader(self.args.pcap_file)

    def run(self):
        """
        Run the frame producer.
        """
        self.load_pcap()
        self.send_frames()

    def load_pcap(self):
        """
        Load frame packets from a packet capture file.
        """

        # Set up packet capture counters
        total_packets = 0
        total_bytes = 0
        current_frame_num = -1
        current_subframe_num = -1

        # Initialise current frame
        current_frame = None

        logging.info(
            "Extracting EXCALIBUR frame packets from PCAP file %s",
            self.args.pcap_file.name
        )

        # Loop over packets in capture
        for _, buf in self.pcap:

            # Extract Ethernet, IP and UDP layers from packet buffer
            eth_layer = dpkt.ethernet.Ethernet(buf)
            ip_layer = eth_layer.data
            udp_layer = ip_layer.data

            # Unpack the packet header
            (subframe_ctr, pkt_ctr) = struct.unpack('<II', udp_layer.data[:8])

            # If there is a SOF marker in the packet header, increment the current subframe and
            # handle content, starting a new frame as necessary
            if pkt_ctr & ExcaliburFrame.SOF_MARKER:
                logging.debug(
                    "Got SOF marker for subframe %d at packet %d",
                    subframe_ctr, total_packets
                )

                # Increment the current subframe index, modulo the number of subframes expected
                current_subframe_num = (current_subframe_num + 1) % ExcaliburFrame.NUM_SUBFRAMES

                # If now on the first subframe of a new frame, handle accordingly
                if current_subframe_num == 0:

                    # Check SOF and EOF count on previous frame before switching to new frame
                    if current_frame is not None:
                        if current_frame.num_sofs_seen() != ExcaliburFrame.NUM_SUBFRAMES:
                            logging.warning(
                                'Frame %d had incorrect number of SOF markers: %d',
                                current_frame_num, current_frame.num_sofs_seen()
                            )
                        if current_frame.num_eofs_seen() != ExcaliburFrame.NUM_SUBFRAMES:
                            logging.warning(
                                'Frame %d had incorrect number of EOF markers: %d',
                                current_frame_num, current_frame.num_eofs_seen()
                            )

                    current_frame_num += 1
                    logging.debug(
                        "Appending new frame %d to frame packet buffer", current_frame_num
                    )

                    # Create a new frame, set it to be the current one and append to the frame list
                    current_frame = ExcaliburFrame(current_frame_num)
                    self.frames.append(current_frame)

                # Update the SOF tracking in the frame
                current_frame.add_sof(subframe_ctr)

            # If there is an EOF marker, handle accordingly
            if pkt_ctr & ExcaliburFrame.EOF_MARKER:

                # Update the EOF tracking in the frame
                current_frame.add_eof(subframe_ctr)

                # Extract the frame number from the frame trailer in the packet data and update
                # tracking in the current frame
                trailer_frame_ctr = struct.unpack('<Q', udp_layer.data[-8:])[0]
                logging.debug(
                    "Got EOF marker for subframe %d at packet %d "
                    "with trailer frame number %d",
                    subframe_ctr, total_packets, trailer_frame_ctr
                )
                current_frame.set_trailer_frame_num(trailer_frame_ctr)

            # Append packet data to current frame
            current_frame.append_packet(udp_layer.data)

            # Increment total packet and byte count
            total_packets += 1
            total_bytes += len(udp_layer.data)

        logging.info(
            "Found %d frames in file with a total of %d packets and %d bytes",
            len(self.frames), total_packets, total_bytes
        )

    def send_frames(self):
        """
        Send loaded frames over UDP socket.
        """

        # Determine number of frames to send. Either number specified in argument or, if default (0)
        # all the frames found in the specified capture file
        if self.args.num_frames == 0:
            frames_to_send = len(self.frames)
        else:
            frames_to_send = self.args.num_frames

        logging.info(
            "Sending %d frames to destination %s:%d ...",
            frames_to_send, self.args.ip_addr, self.args.port
        )

        # Create the UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if udp_socket is None:
            logging.error("Failed to open UDP socket")
            return

        # Initialise frame send counters
        total_frames_sent = 0
        total_packets_sent = 0
        total_bytes_sent = 0
        total_packets_dropped = 0

        # Loop over the number of frames to be sent
        for frame in range(frames_to_send):

            # Get the appropriate frame from the frame buffer
            frame_idx = frame % len(self.frames)
            current_frame = self.frames[frame_idx]

            frame_bytes_sent = 0
            frame_packets_sent = 0
            frame_packets_dropped = 0

            frame_start_time = time.time()

            # Loop over packets in current frame
            for packet_idx, packet in enumerate(current_frame.packets):

                # If a drop fraction option was specified, decide if the packet should be dropped
                if self.args.drop_frac > 0.0:
                    if random.uniform(0.0, 1.0) < self.args.drop_frac:
                        frame_packets_dropped += 1
                        continue

                # If a drop list was specified and this packet is in it, drop the packet
                if self.args.drop_list is not None:
                    if packet_idx in self.args.drop_list:
                        frame_packets_dropped +=1
                        continue

                # Send the packet over the UDP socket
                try:
                    frame_bytes_sent += udp_socket.sendto(
                        packet, (self.args.ip_addr, self.args.port)
                    )
                    frame_packets_sent += 1
                except socket.error as exc:
                    logging.error("Got error sending frame packet: %s", exc)
                    break

            logging.debug(
                "Sent %d bytes in %d packets for frame %d, dropping %d packets (%.1f%%)",
                frame_bytes_sent, frame_packets_sent, frame, frame_packets_dropped,
                (float(frame_packets_dropped)/(frame_packets_dropped + frame_packets_sent))*100.0
            )

            # Update counters
            total_frames_sent += 1
            total_packets_sent += frame_packets_sent
            total_packets_dropped += frame_packets_dropped
            total_bytes_sent += frame_bytes_sent

            # Calculate wait time and sleep so that frames are sent at requested intervals
            frame_end_time = time.time()
            wait_time = (frame_start_time + self.args.tx_interval) - frame_end_time
            if wait_time > 0:
                time.sleep(wait_time)

        logging.info(
            "Sent %d frames with a total of %d packets and %d bytes, dropping %d packets (%.1f%%)",
            total_frames_sent, total_packets_sent, total_bytes_sent, total_packets_dropped,
            (float(total_packets_dropped) / (total_packets_dropped + total_packets_sent))*100.0
        )

        udp_socket.close()

if __name__ == '__main__':

    ExcaliburFrameProducer().run()
