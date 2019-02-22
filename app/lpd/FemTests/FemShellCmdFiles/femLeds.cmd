open 192.168.1.10 6969
for i in range(0, 10)
  for j in range(0, 255)
    write raw long 0x81440000 $j
  end
end
close
exit
