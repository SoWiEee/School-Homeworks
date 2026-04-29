package javaHw;
import java.util.Scanner;

public class CreditLimitCal {
	public static void main(String[] args) {
		int account, oldBalance, charges, credits, creditLimit, newBalance;
		Scanner jin = new Scanner(System.in);

		System.out.println("Enter Account Number: ");
		account = jin.nextInt();

		System.out.println("Enter Balance: ");
		oldBalance = jin.nextInt();

		System.out.println("Enter Charges: ");
		charges = jin.nextInt();

		System.out.println("Enter Credits: ");
		credits = jin.nextInt();

		System.out.println("Enter Credit Limit: ");
		creditLimit = jin.nextInt();

		newBalance = oldBalance + charges - credits;

		System.out.println("New balance is " + newBalance);
		if (newBalance > creditLimit)
			System.out.println("Credit Limit Exceeded");
	}
}
