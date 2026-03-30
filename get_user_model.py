with open("kampus-stie-samarinda-21 ( idcloudhost - Third Layer of Quality Control ).py", "r") as f:
    lines = f.readlines()
for i in range(130, 140):
    print(f"{i+1}: {lines[i].strip()}")
