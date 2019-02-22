open 192.168.1.10 6969
for i in range(0, 100)
  for j in [1,2,4,8,16,32,64,128]
    write raw long 0x81440000 $j
    wait 0.05
  end
  for k in [128,64,32,16,8,4,2,1]
    write raw long 0x81440000 $k
    wait 0.05	
  end
end
close
wait 1
exit
