def addzero(n) { return n + 0; }
n = addzero(1) + addzero(2);
n = addzero(addzero(0));
print(n);
