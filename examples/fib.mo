def fib(n) {
    if (n==1){return 1;}(n==2){return 2;}(n>2){return fib(n-1)+fib(n-2);}
}
print(fib(10));
