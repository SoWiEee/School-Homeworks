public class SavingsAccount {
	private static double annualInterestRate = 0;
	private double savingBalance;

	public SavingsAccount(double savingBalance) {
		this.savingBalance = savingBalance;
	}

	public void calculateMonthInterest() {
		savingBalance += savingBalance * (annualInterestRate / 12);
	}

	public static void modifyInterestRate(double rate) {
		annualInterestRate = (rate >= 0 && rate <= 1) ? rate : 0.04;
	}

	@Override
	public String toString() {
		return String.format("%s: %.2f\n", "Balance", this.savingBalance);
	}
}
