
import java.util.Scanner;

public class Sales {

    public static void main(String[] args) {
        Scanner input = new Scanner(System.in);

        double[] array = {239.99,129.75,99.95,350.89}; //declare an array

        System.out.println("Enter the price of the merchandise=>");
        double value = input.nextDouble();
        double total = 200 + (value * 0.09);
        System.out.println(total);
    }
}