with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    lines = f.readlines()
for i in range(103, 112):
    print(f"{i+1}: {lines[i].strip()}")

print("---")
for i in range(191, 206):
    print(f"{i+1}: {lines[i].strip()}")
