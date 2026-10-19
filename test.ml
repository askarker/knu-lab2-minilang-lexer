// вычисление факториала
fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
let x = 5;
let pi = 3.14;
/* многострочный
   комментарий */
print("fact(5) = ", fact(x));
while (x != 0 && true) { x = x - 1; }
