public class SavingsAccountTest {

	public static void main(String[] args) {
		SavingsAccount saver1 = new SavingsAccount(2000.00);
		SavingsAccount saver2 = new SavingsAccount(3000.00);
		SavingsAccount.modifyInterestRate(.04);

		for (int i = 1; i < 13; i++) {
			System.out.printf("Month %d\n", i);
			saver1.calculateMonthInterest();
			saver2.calculateMonthInterest();
			System.out.printf("Saver1\n%s", saver1);
			System.out.printf("Saver2\n%s\n", saver2);
		}

		SavingsAccount.modifyInterestRate(.05);
		saver1.calculateMonthInterest();
		saver2.calculateMonthInterest();
		System.out.println("Next month: ");
		System.out.printf("Saver1\n%s", saver1);
		System.out.printf("Saver2\n%s", saver2);
	}

}
