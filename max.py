print("x", end="\t")
for col in range(1, 13):
    print(col, end="\t")
print()
 
for row in range(1, 13):
    print(row, end="\t")
    # แก้ไขการย่อหน้า (Indentation) ในบรรทัดด้านล่างนี้ให้ตรงกัน
    for col in range(1, 13):
        result = row * col
        print(result, end="\t")
    print()
