import java.util.Scanner;

public class Payment {
	private double itemValue[] = {239.99, 129.75, 99.95, 350.89}; /* Value of each item.**/
	private int item[] = new int[LEN]; /* Number of sales of each item.**/
	private double pay; /* Payment of last week of salesperson.**/
	public static final int LEN = 4;
	/* Constructor for initialize item array and payment.**/
	Payment()
	{ 
		for(int i = 0; i < 4; ++i) {
			item[i] = 0;
		}
		pay = 0;
	}
	/* Check whether every value in array are positive or not**/
	private boolean isInvalid(int[] array, int n) {
		for (int i = 0; i < n; ++i) {
			/* If any value in array less then 0**/
			if(array[i] <0) { 
				return true;
			}
		}
		/* Every value are checked.**/
		return false;
	}
	/* Set each item's sales.**/
	public boolean SetSold(int[] item) { 
		/* Check whether input is value or not.**/
		if(isInvalid(item, LEN)) { /* Invalid**/
			for(int i = 0; i < LEN; ++i) { /* Set every sales to 0.**/
				this.item[i] = 0;
			}
			/* Present user input data is invalid.**/
			System.out.println("Input conlude negative value, please enter again.");
			return true;
		}
		else {
			for(int i = 0; i < LEN; ++i) { /* Set each sales**/
				this.item[i] = item[i];
			}
			return false;
		}
	}
	/* 計算收益並顯示收益 **/
	public void DisplayEarning() { 
		/* Calculate sales.**/
		for (int i = 0 ; i < LEN; ++i) { 
			pay += itemValue[i] * item[i]; /* 價格乘上數量**/
		}
		pay = (0.09 * pay) + 200; /* Earning = 9% of sales + 200**/
		System.out.println("Payment of last week: " + pay); /* Display earning.**/
	}
	
	/* main function **/
	public static void main(String[] args) {
		Payment salesp = new Payment(); /* Salesperson**/
		Scanner sc = new Scanner(System.in); /* Scanner**/
		int item[] = new int[LEN]; /* Sales of items**/
		boolean error; /* Error variable to define error happened.**/
		/* Get sales of each item until valid input.**/
		do {
			error = false; /* No error yet**/
			/* Present user to enter number to calculate earning.**/
			System.out.println("Please enter number of sold of each items >> ");
			for (int i = 0; i < LEN; ++i) {
				int itemTemp = sc.nextInt();
				item[i] = itemTemp;
			}
			error = salesp.SetSold(item); /* Set sales and check error.**/
		} while(error);
		sc.close(); /* Close scanner**/
		salesp.DisplayEarning(); /* Display earning**/
	}

}
