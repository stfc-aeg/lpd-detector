open 127.0.0.1 5000
write raw long 0x1000 0x12345
read raw long 0x1000 1
write raw long 0x1003 0x67890
read raw long 0x1000 4
for i in range(0, 100)
  write raw long $i $i
end
read raw long 0 100
close
exit
