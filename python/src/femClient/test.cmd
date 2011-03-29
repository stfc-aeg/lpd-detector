open 127.0.0.1 5000
write 1 2 3 4
write 5 6 7 8
write 1001 1002 1003 1004
for i in range(0, 10000)
  write $i $i $i 1000
end
close
exit
