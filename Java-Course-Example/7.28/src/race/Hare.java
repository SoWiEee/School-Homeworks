package race;

/* Hare class
 * move
 * get position
 * */

public class Hare {
	private int position; /* position of hare*/
	
	/* Constructor, initialize position at start.*/
	public Hare() {
		position = 1;
	}
	
	/* Move by randomly*/
	public void move(int num) {
		if(num < 2) {
			sleep();
		}
		else if(num >= 2 && num < 4) {
			bigHop();
		}
		else if(num >= 4 && num < 5){
			bigSlip();
		}
		else if(num >=5 && num < 8) {
			smallHop();
		}
		else {
			smallSlip();
		}
	}
	/* Move types*/
	public void sleep() {
		
	}
	public void bigHop() {
		position += 9;
	}
	public void bigSlip() {
		if(position > 13) {
			position -= 12;
		}
		else {
			position = 1;
		}
	}
	public void smallHop() {
		position += 1;
	}
	public void smallSlip() {
		if(position > 3) {
			position -= 2;
		}
		else {
			position = 1;
		}
	}
	/* Get current position.*/
	public int getPos() {
		return position;
	}
}
