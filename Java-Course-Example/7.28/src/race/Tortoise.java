package race;

/* Tortoise class
 * move
 * get position
 * */

public class Tortoise {
	private int position; /* position of Tortoise*/
	
	/* Constructor, initialize position to start.*/
	public Tortoise() {
		position = 1;
	}
	/* Move by randomly*/
	public void move(int num) {
		if(num < 5) {
			fastPlod();
		}
		else if(num >=5 && num < 7) {
			slip();
		}
		else {
			slowPlod();
		}
	}
	/* Move types*/
	public void fastPlod() {
		position += 3;
	}
	public void slip() {
		if(position > 7) {
			position -= 6;
		}
		else {
			position = 1;
		}
	}
	public void slowPlod() {
		position += 1;
	}
	/* Get current position.*/
	public int getPos() {
		return position;
	}
}
