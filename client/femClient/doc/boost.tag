<?xml version='1.0' encoding='ISO-8859-1' standalone='yes' ?>
<tagfile>
  <compound kind="file">
    <name>dataTypes.h</name>
    <path>/Users/tcn/Develop/fem/femClient/include/</path>
    <filename>data_types_8h</filename>
    <member kind="typedef">
      <type>unsigned char</type>
      <name>u8</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>ed742c436da53c1080638ce6ef7d13de</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>unsigned short</type>
      <name>u16</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>9e6c91d77e24643b888dbd1a1a590054</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>unsigned int</type>
      <name>u32</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>10e94b422ef0c20dcdec20d31a1f5049</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>unsigned long long</type>
      <name>u64</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>d758b7a5c3f18ed79d2fcd23d9f16357</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>char</type>
      <name>s8</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>2ff401e087cf786c38a6812723e94473</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>short</type>
      <name>s16</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>2e9bf6983da73775aa86158c825bf777</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>int</type>
      <name>s32</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>a62c75d314a0d1f37f79c4b73b2292e2</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>long long</type>
      <name>s64</name>
      <anchorfile>data_types_8h.html</anchorfile>
      <anchor>93680f46d09022794e3923824923b42b</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>FemClient.h</name>
    <path>/Users/tcn/Develop/fem/femClient/include/</path>
    <filename>_fem_client_8h</filename>
    <includes id="_fem_transaction_8h" name="FemTransaction.h" local="yes" imported="no">FemTransaction.h</includes>
    <includes id="_fem_exception_8h" name="FemException.h" local="yes" imported="no">FemException.h</includes>
    <class kind="class">FemClientException</class>
    <class kind="class">FemClient</class>
    <member kind="enumeration">
      <name>femClientErrorCode</name>
      <anchor>4e3fb9052c4f044eb17ca09fe4cd2f6c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>femClientOK</name>
      <anchor>4e3fb9052c4f044eb17ca09fe4cd2f6c5627dec9e6130671631cc906ac75c0db</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>femClientDisconnected</name>
      <anchor>4e3fb9052c4f044eb17ca09fe4cd2f6c8021633cc018c4db7096490ecb4aacd8</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>femClientTimeout</name>
      <anchor>4e3fb9052c4f044eb17ca09fe4cd2f6cd9c77571c277bd04e4430dbed2e6c88a</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>femClientSendMismatch</name>
      <anchor>4e3fb9052c4f044eb17ca09fe4cd2f6c8678bbffcadee51238cc45fcae50587e</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>FemException.h</name>
    <path>/Users/tcn/Develop/fem/femClient/include/</path>
    <filename>_fem_exception_8h</filename>
    <class kind="class">FemException</class>
    <member kind="define">
      <type>#define</type>
      <name>FEM_EXCEPTION_LOCATION</name>
      <anchorfile>_fem_exception_8h.html</anchorfile>
      <anchor>0b2962bf622c95f235c0bc04237a6836</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>int</type>
      <name>FemErrorCode</name>
      <anchorfile>_fem_exception_8h.html</anchorfile>
      <anchor>8cd94f8fb31246d58bca7bda8e830279</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>FemTransaction.h</name>
    <path>/Users/tcn/Develop/fem/femClient/include/</path>
    <filename>_fem_transaction_8h</filename>
    <includes id="protocol_8h" name="protocol.h" local="yes" imported="no">protocol.h</includes>
    <class kind="class">FemTransaction</class>
  </compound>
  <compound kind="file">
    <name>protocol.h</name>
    <path>/Users/tcn/Develop/fem/femClient/include/</path>
    <filename>protocol_8h</filename>
    <includes id="data_types_8h" name="dataTypes.h" local="yes" imported="no">dataTypes.h</includes>
    <class kind="struct">protocol_header</class>
    <member kind="define">
      <type>#define</type>
      <name>MAX_PAYLOAD_SIZE</name>
      <anchorfile>protocol_8h.html</anchorfile>
      <anchor>6303f7392a2d06be5a121c54278d561b</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>PROTOCOL_MAGIC_WORD</name>
      <anchorfile>protocol_8h.html</anchorfile>
      <anchor>d8903cf2b6e47acea41c727c6ae12e0e</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>CBIT</name>
      <anchorfile>protocol_8h.html</anchorfile>
      <anchor>3d8ab8b754709cdac3275a65455c354b</anchor>
      <arglist>(val, bit)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>SBIT</name>
      <anchorfile>protocol_8h.html</anchorfile>
      <anchor>5cb95f4ae1caa7226b585f7e8a74e2f7</anchor>
      <arglist>(val, bit)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>CMPBIT</name>
      <anchorfile>protocol_8h.html</anchorfile>
      <anchor>23d935c5655778c5b7bacb718af6bc96</anchor>
      <arglist>(val, bit)</arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>DUMPHDR</name>
      <anchorfile>protocol_8h.html</anchorfile>
      <anchor>7e99daeb7b7b6fc1e3dcdf199b52d765</anchor>
      <arglist>(hdr)</arglist>
    </member>
    <member kind="enumeration">
      <name>protocol_commands</name>
      <anchor>894ed69869e79f26159afd9dfc6d92ea</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CMD_UNSUPPORTED</name>
      <anchor>894ed69869e79f26159afd9dfc6d92ea925e3fdc926fbb3640fb681acf217564</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CMD_ACCESS</name>
      <anchor>894ed69869e79f26159afd9dfc6d92ea0e629ef3b073557195ed08608ba6de6c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>CMD_INTERNAL</name>
      <anchor>894ed69869e79f26159afd9dfc6d92ea6665d8f0bcf614404cc57821e7be1d8c</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <name>protocol_bus_type</name>
      <anchor>07b31707bf8aa463d26ef51bb92d835e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BUS_UNSUPPORTED</name>
      <anchor>07b31707bf8aa463d26ef51bb92d835e4bfb1b07fe85616244a6486b48ca22f7</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BUS_EEPROM</name>
      <anchor>07b31707bf8aa463d26ef51bb92d835e25474ecb9eeffa63b636f7d84256afb2</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BUS_I2C</name>
      <anchor>07b31707bf8aa463d26ef51bb92d835ef3fee81c16c44acf998b3d6818a22373</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BUS_RAW_REG</name>
      <anchor>07b31707bf8aa463d26ef51bb92d835ee3608c5a7048938db2fa88118d37dbd5</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>BUS_RDMA</name>
      <anchor>07b31707bf8aa463d26ef51bb92d835e42dc5b7a4c4a476c7081a6a883c85488</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <name>protocol_data_width</name>
      <anchor>efa895dbb78e0303b8849f1aa2b55640</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>WIDTH_UNSUPPORTED</name>
      <anchor>efa895dbb78e0303b8849f1aa2b5564077f8067b69f5205174ee6c9c62188f94</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>WIDTH_BYTE</name>
      <anchor>efa895dbb78e0303b8849f1aa2b5564083d300cfb31276764704daed2c47d9f9</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>WIDTH_WORD</name>
      <anchor>efa895dbb78e0303b8849f1aa2b556402f4c7c06db9fd92819d6e4d6149ef47e</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>WIDTH_LONG</name>
      <anchor>efa895dbb78e0303b8849f1aa2b556401ff75efd98e35ad31fd9532a056f9ce6</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumeration">
      <name>protocol_status</name>
      <anchor>d1a0c3585a41c5e2de27c47ad0023f99</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_UNSUPPORTED</name>
      <anchor>d1a0c3585a41c5e2de27c47ad0023f99e093dca0e6aed01bfcec32f9ef64ccd0</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_READ</name>
      <anchor>d1a0c3585a41c5e2de27c47ad0023f990bd62d2c19c771fedb1c6459ff576756</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_WRITE</name>
      <anchor>d1a0c3585a41c5e2de27c47ad0023f99d7e5fc0be7f7577c4cd289a483a31a8f</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_ACK</name>
      <anchor>d1a0c3585a41c5e2de27c47ad0023f992e95f684d24fa226fd276ee1c6ba73c1</anchor>
      <arglist></arglist>
    </member>
    <member kind="enumvalue">
      <name>STATE_NACK</name>
      <anchor>d1a0c3585a41c5e2de27c47ad0023f99d145ee6b5436f3aa329c04b8e6a5560b</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>FemClient.cpp</name>
    <path>/Users/tcn/Develop/fem/femClient/src/</path>
    <filename>_fem_client_8cpp</filename>
    <includes id="_fem_client_8h" name="FemClient.h" local="yes" imported="no">FemClient.h</includes>
    <includes id="_fem_exception_8h" name="FemException.h" local="yes" imported="no">FemException.h</includes>
  </compound>
  <compound kind="file">
    <name>FemClientMain.cpp</name>
    <path>/Users/tcn/Develop/fem/femClient/src/</path>
    <filename>_fem_client_main_8cpp</filename>
    <includes id="_fem_client_8h" name="FemClient.h" local="yes" imported="no">FemClient.h</includes>
    <includes id="_fem_transaction_8h" name="FemTransaction.h" local="yes" imported="no">FemTransaction.h</includes>
    <member kind="function">
      <type>int</type>
      <name>main</name>
      <anchorfile>_fem_client_main_8cpp.html</anchorfile>
      <anchor>0ddf1224851353fc92bfbff6f499fa97</anchor>
      <arglist>(int argc, char *argv[])</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>FemException.cpp</name>
    <path>/Users/tcn/Develop/fem/femClient/src/</path>
    <filename>_fem_exception_8cpp</filename>
    <includes id="_fem_exception_8h" name="FemException.h" local="yes" imported="no">FemException.h</includes>
  </compound>
  <compound kind="file">
    <name>FemTransaction.cpp</name>
    <path>/Users/tcn/Develop/fem/femClient/src/</path>
    <filename>_fem_transaction_8cpp</filename>
    <includes id="_fem_transaction_8h" name="FemTransaction.h" local="yes" imported="no">FemTransaction.h</includes>
    <member kind="function">
      <type>std::ostream &amp;</type>
      <name>operator&lt;&lt;</name>
      <anchorfile>_fem_transaction_8cpp.html</anchorfile>
      <anchor>e9b19ff727656f72ca5e4b566bb80c3f</anchor>
      <arglist>(std::ostream &amp;aOut, const FemTransaction &amp;aTrans)</arglist>
    </member>
  </compound>
  <compound kind="class">
    <name>FemClient</name>
    <filename>class_fem_client.html</filename>
    <member kind="function">
      <type></type>
      <name>FemClient</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>ed11b03dbcde35385665defc64541bcd</anchor>
      <arglist>(char *aHostString, int aPortNum, unsigned int aTimeoutInMsecs=0)</arglist>
    </member>
    <member kind="function" virtualness="virtual">
      <type>virtual</type>
      <name>~FemClient</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>5acf51116333569ed59ef5b334301f17</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>setTimeout</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>2506e398e7846d4185ebc11337ee2c79</anchor>
      <arglist>(unsigned int aTimeoutInMsecs)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>setTimeout</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>2bcd4efda23dd6dc68c658532a93d87e</anchor>
      <arglist>(float aTimeoutInSecs)</arglist>
    </member>
    <member kind="function">
      <type>size_t</type>
      <name>send</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>519ec16b1429674a196173267d2f5cb0</anchor>
      <arglist>(FemTransaction aTrans)</arglist>
    </member>
    <member kind="function">
      <type>FemTransaction</type>
      <name>receive</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>18e93a5a9801242684000945bf2093f7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>runIoService</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>9d2c72f239fcd2abf206ecb45cc63c83</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" protection="private">
      <type>std::size_t</type>
      <name>receivePart</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>cb2f3d9cd46285ffd7cde119746808a9</anchor>
      <arglist>(std::vector&lt; u8 &gt; &amp;buffer, boost::system::error_code &amp;error)</arglist>
    </member>
    <member kind="function" protection="private">
      <type>void</type>
      <name>checkDeadline</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>2d8e6910d30458e527bb1da26fa6e6fb</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" protection="private" static="yes">
      <type>static void</type>
      <name>asyncCompletionHandler</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>3e90d6ce358c82e0830024583a012108</anchor>
      <arglist>(const boost::system::error_code &amp;ec, std::size_t length, boost::system::error_code *out_ec, std::size_t *out_length)</arglist>
    </member>
    <member kind="variable" protection="private">
      <type>boost::asio::io_service</type>
      <name>mIoService</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>ce8d84d6be2da18ee1277aedc12f8378</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>tcp::endpoint</type>
      <name>mEndpoint</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>53761cfcd52d26d374f2c26e3f5524a7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>tcp::socket</type>
      <name>mSocket</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>9e9a38ed6ac4fc9856d3d93b545e9be3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>boost::asio::deadline_timer</type>
      <name>mDeadline</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>1e655ce765698afc1284439034aa0d2e</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>unsigned int</type>
      <name>mTimeout</name>
      <anchorfile>class_fem_client.html</anchorfile>
      <anchor>7684f4061706504e6862952944ab3d41</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="class">
    <name>FemClientException</name>
    <filename>class_fem_client_exception.html</filename>
    <base>FemException</base>
    <member kind="function">
      <type></type>
      <name>FemClientException</name>
      <anchorfile>class_fem_client_exception.html</anchorfile>
      <anchor>092a88e07df3cce486bb6f77a9a445c1</anchor>
      <arglist>(const std::string aExText)</arglist>
    </member>
    <member kind="function">
      <type></type>
      <name>FemClientException</name>
      <anchorfile>class_fem_client_exception.html</anchorfile>
      <anchor>2fc2ca9ce89def3916ed319c009de6c7</anchor>
      <arglist>(const FemErrorCode aExCode, const std::string aExText)</arglist>
    </member>
  </compound>
  <compound kind="class">
    <name>FemException</name>
    <filename>class_fem_exception.html</filename>
    <member kind="function">
      <type></type>
      <name>FemException</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>80802dcee08da20e1ed85aa48190b96e</anchor>
      <arglist>(const std::string aExText)</arglist>
    </member>
    <member kind="function">
      <type></type>
      <name>FemException</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>3e8345a70b41fc5e0bf2ab42ed678f63</anchor>
      <arglist>(const FemErrorCode aExCode, const std::string aExText)</arglist>
    </member>
    <member kind="function">
      <type></type>
      <name>FemException</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>c2076611a862d82efc2ef8be827dad3e</anchor>
      <arglist>(const FemErrorCode aExCode, const std::string aExText, const std::string aExFunc, const std::string aExFile, const int aExLine)</arglist>
    </member>
    <member kind="function" virtualness="virtual">
      <type>virtual</type>
      <name>~FemException</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>9be202ebef59ffe3a4f544977d1fceed</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" virtualness="virtual">
      <type>virtual const char *</type>
      <name>what</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>c720b1d1d86efb3bf053f57e9bba6578</anchor>
      <arglist>() const</arglist>
    </member>
    <member kind="function" virtualness="virtual">
      <type>virtual const char *</type>
      <name>where</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>b55e6876bf0cfce165a209c01332c47f</anchor>
      <arglist>() const</arglist>
    </member>
    <member kind="function" virtualness="virtual">
      <type>virtual FemErrorCode</type>
      <name>which</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>91c4c1a951daf11744dcde51bb540519</anchor>
      <arglist>() const</arglist>
    </member>
    <member kind="variable" protection="private">
      <type>const FemErrorCode</type>
      <name>mExCode</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>d363ec23f2b48023c9b1e4e68393a8dd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>const std::string</type>
      <name>mExText</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>972596a13cd3836fe6197555de868da7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>const std::string</type>
      <name>mExFunc</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>47819c6326235101a3d2638224c66d91</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>const std::string</type>
      <name>mExFile</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>4bdcdc8b873910c24118a7665f0cae0d</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>const int</type>
      <name>mExLine</name>
      <anchorfile>class_fem_exception.html</anchorfile>
      <anchor>ed12d694e36ec6b59bd2cc17f1445833</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="class">
    <name>FemTransaction</name>
    <filename>class_fem_transaction.html</filename>
    <member kind="function">
      <type></type>
      <name>FemTransaction</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>97d2f0248d0e69925287a362da9f0fe0</anchor>
      <arglist>(u8 cmd=CMD_UNSUPPORTED, u8 bus=BUS_UNSUPPORTED, u8 width=WIDTH_UNSUPPORTED, u8 state=STATE_UNSUPPORTED, u32 address=0, u8 *payload=0, u32 payloadSize=0)</arglist>
    </member>
    <member kind="function">
      <type></type>
      <name>FemTransaction</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>e1ead69895ad28a0523a7cb6e34245c2</anchor>
      <arglist>(const std::vector&lt; u8 &gt; &amp;byteStream)</arglist>
    </member>
    <member kind="function" virtualness="virtual">
      <type>virtual</type>
      <name>~FemTransaction</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>d8d1bfa88e100a4cc9221ac84a3a7155</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="function">
      <type>std::vector&lt; u8 &gt;</type>
      <name>encode</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>f8bb7c2705605d1c49c0c4ee3cbc2259</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>appendPayload</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>9cc323da5acda56de415a0216941e394</anchor>
      <arglist>(u8 *aPayload, u32 aPayloadLen)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>appendPayloadFromStream</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>b974aa79efedb11747580b83d7c70408</anchor>
      <arglist>(const std::vector&lt; u8 &gt; &amp;byteStream, size_t offset=0)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>clearPayload</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>455042d438dd919ea5abdbede00be169</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>std::vector&lt; u8 &gt;</type>
      <name>getPayload</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>b5d0a70226d7fb0133ea55bdb28bb0dd</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>bool</type>
      <name>payloadIncomplete</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>d09755a33ce8889b6cf42e8dd523c474</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function">
      <type>size_t</type>
      <name>payloadRemaining</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>1729ba996aec7cb3e985efdf3a57dea7</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" static="yes">
      <type>static const size_t</type>
      <name>headerLen</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>3d83ed22d7f9fd278cae0c4f9f9a2baa</anchor>
      <arglist>(void)</arglist>
    </member>
    <member kind="function" protection="private">
      <type>void</type>
      <name>u16Encode</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>39252f6a0188d5cef06e6d168626c86b</anchor>
      <arglist>(std::vector&lt; u8 &gt; &amp;aEncoded, u16 aValue)</arglist>
    </member>
    <member kind="function" protection="private">
      <type>void</type>
      <name>u32Encode</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>61a14f6dfacbad073fdb67b7e7f22f2a</anchor>
      <arglist>(std::vector&lt; u8 &gt; &amp;aEncoded, u32 aValue)</arglist>
    </member>
    <member kind="function" protection="private">
      <type>void</type>
      <name>u16Decode</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>e3ea88ea7f9c2b43aa70450ca035b5b7</anchor>
      <arglist>(std::vector&lt; u8 &gt; &amp;aDecoded, u16 aValue)</arglist>
    </member>
    <member kind="function" protection="private">
      <type>void</type>
      <name>u32Decode</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>e903444fcfaefe007e3deaea47af61af</anchor>
      <arglist>(std::vector&lt; u8 &gt; &amp;aDecoded, u32 aValue)</arglist>
    </member>
    <member kind="variable" protection="private">
      <type>protocol_header</type>
      <name>mHeader</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>db6d8162428a9d79b804e35fb270a6ba</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>std::vector&lt; u8 &gt;</type>
      <name>mPayload</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>59d0450d313f9c27fa20fb88ef1246d1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>size_t</type>
      <name>mPayloadRemaining</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>4d66d34f2b8e168f196cb922076823a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="friend">
      <type>friend std::ostream &amp;</type>
      <name>operator&lt;&lt;</name>
      <anchorfile>class_fem_transaction.html</anchorfile>
      <anchor>e9b19ff727656f72ca5e4b566bb80c3f</anchor>
      <arglist>(std::ostream &amp;aOut, const FemTransaction &amp;aTrans)</arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>protocol_header</name>
    <filename>structprotocol__header.html</filename>
    <member kind="variable">
      <type>u32</type>
      <name>magic</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>6cc631800827177465f93384a28cba99</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>u8</type>
      <name>command</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>1f10d1850eb5e5294c47448b86a3016c</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>u8</type>
      <name>bus_target</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>29f8bf00f930063cf5ecc317896a34cd</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>u8</type>
      <name>data_width</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>b50e6042d25eeca64ee04a0562613868</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>u8</type>
      <name>status</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>33aaa1c5187d29e32e2c1589725c1260</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>u32</type>
      <name>address</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>8a734d8b92b6cce74b18cb9cf7cc57a4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>u32</type>
      <name>payload_sz</name>
      <anchorfile>structprotocol__header.html</anchorfile>
      <anchor>07102dc09889fe0261ce4db3ad5cd0c4</anchor>
      <arglist></arglist>
    </member>
  </compound>
</tagfile>
