import java.util.InputMismatchException;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n1, n2;
        double r;
        boolean flag = false;

        while (true) {
            try {
                System.out.println("Enter a number: ");
                n1 = sc.nextInt();
                System.out.println("Enter a number: ");
                n2 = sc.nextInt();
            } catch (InputMismatchException e) {
                System.out.println("[X] Result is not an integer!");
                System.out.println("Please enter numbers again!");
                // 清除錯誤輸入
                sc.next();
                continue;
            }

            try {
                if(n2 == 0){
                    throw new DivideByZero("[X] Divide by zero!");
                }
                r = (double) n1 / n2;
                System.out.println("Result: " + r);
            } catch (DivideByZero e) {
                // 捕捉這種例外
                System.out.println(e.getMessage());
                flag = true;
            } catch (Exception e) {
                // 捕捉這種例外
                System.out.println("Error: " + e.getMessage());
                flag = true;
            }finally {
                // 一定會執行到此區塊
                if(flag){
                    System.out.println("Please enter numbers again!");
                    flag = false;
                }else{
                    break;
                }
            }
        }
        sc.close();
    }
}