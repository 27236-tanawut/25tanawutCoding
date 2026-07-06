print("โปรแกรมแสดงสูตรคูณตั้งแต่เริ่มต้นถึงสิ้นสุด\n")
start = int(input("กรุณากรอกแม่สูตรคูณเริ่มต้น: "))
end = int(input("กรุณากรอกแม่สูตรคูณสิ้นสุด: "))

for j in range(start, end + 1):
    print("สูตรคูณของ", j) 
    for i in range(1, 13):
        print(j, "x", i, "=", j * i)
    
    print() 

print("ธนาวุฒิ สาวะรักษ์ เลขที่ 25 ห้อง 4/4")
