file = open("matrix_data.txt", "w")
file.write("testing")
file.close()

file = open("matrix_data.txt", "r")
print(file.read())
