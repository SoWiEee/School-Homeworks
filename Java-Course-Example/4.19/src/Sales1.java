
import java.util.Scanner;

public class Sales1 {
 public static double item1 (int sum) {//GET
  return 239.99 * sum * 0.09;
 }
 
 public static double item2 (int sum) {//GET
  return 129.75 * sum * 0.09;
 }
 
 public static double item3 (int sum) {//GET
  return 99.95 * sum * 0.09;
 }
 
 public static double item4 (int sum) {//GET
  return 350.89 * sum * 0.09;
 }
 
    public static void main(String[] args) {
        Scanner input = new Scanner(System.in);

        System.out.println("Enter the number of item1 be sold:");
        int value1 = input.nextInt();
        System.out.println("Enter the number of item2 be sold:");
        int value2 = input.nextInt();
        System.out.println("Enter the number of item3 be sold:");
        int value3 = input.nextInt();
        System.out.println("Enter the number of item4 be sold:");
        int value4 = input.nextInt();
        
        System.out.printf("The salespeople will receive $%.2f this week",200 + item1(value1) + item2(value2) + item3(value3) + item4(value4));
    }
}