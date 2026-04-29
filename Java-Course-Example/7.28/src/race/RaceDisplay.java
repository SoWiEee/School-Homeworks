package race;

/* Race display class
 * Display each position of tortoise and hare.
 * */

public class RaceDisplay {
	/* number of left and right bar need to print.*/
	private int leftBar = -1;
	private int rightBar = 70;
	private String bar = "-";
	private String blank = " ";
	
	/* Constructor, no input position.*/
	public RaceDisplay() {
		System.out.println("No race.");
	}
	/* Constructor, display two position.*/
	public RaceDisplay(int pos1, int pos2) {
		/* At different position.*/
		if(pos1 != pos2) {
			/* Print bar from start to slow one.*/
			for (int i = 0; i < leftBar + Math.min(pos1, pos2); ++i) {
				System.out.printf("%s", bar);
			}
			/* Print slow one*/
			if(pos1 < pos2) {
				System.out.printf("T");
			}
			else {
				System.out.printf("H");
			}
			/* Print bar between tortoise and hare.*/
			for (int i = 0; i < Math.min(Math.abs(pos1 - pos2), rightBar - Math.min(pos1, pos2)); ++i) {
				System.out.printf("%s", bar);
			}
			/* Print fast one*/
			if(pos1 < pos2) {
				System.out.printf("H");
			}
			else {
				System.out.printf("T");
			}
			/* Print bar from fast one to goal.*/
			for (int i = 0; i < rightBar - Math.max(pos1, pos2); ++i) {
				System.out.printf("%s", bar);
			}
			System.out.println();
		}
		else {
			/* Same position
			 * Change bar to blank.
			 * */
			/* Print blank from start to slow one.*/
			for (int i = 0; i < leftBar + Math.min(pos1, pos2); ++i) {
				System.out.printf("%s", blank);
			}
			/* Print slow one*/
			if(pos1 < pos2) {
				System.out.printf("T");
			}
			else {
				System.out.printf("H");
			}
			/* Print blank between tortoise and hare.*/
			for (int i = 0; i < Math.min(Math.abs(pos1 - pos2), rightBar - Math.min(pos1, pos2)); ++i) {
				System.out.printf("%s", blank);
			}
			/* Print fast one*/
			if(pos1 < pos2) {
				System.out.printf("H");
			}
			else {
				System.out.printf("T");
			}
			/* Print blank from fast one to goal.*/
			for (int i = 0; i < rightBar - Math.max(pos1, pos2); ++i) {
				System.out.printf("%s", blank);
			}
			/* Display Ouch.*/
			System.out.println("OUCH!!!");
		}
	}
}
