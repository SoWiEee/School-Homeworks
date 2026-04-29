package race;

import java.security.SecureRandom;

public class RaceProcess {
	/* Goal position.*/
	private final int GOAL = 70;
	private SecureRandom randomNumber = new SecureRandom(); /* Generate random number.*/
	private int winner = 1; /* 1: tortoise win, -1: hare win*/
	
	public RaceProcess() {
		/* Start*/
		System.out.println("BANG !!!!!");
		System.out.println("AND THEY'RE OFF !!!!!");
		/* Tortoise and hare.*/
		Tortoise tortoise = new Tortoise();
		Hare hare = new Hare();
		/* Display start position.*/
		RaceDisplay race = new RaceDisplay(tortoise.getPos(), hare.getPos());
		
		/* Display process until goal.*/
		while(checkPos(tortoise, hare) == 0) {
			tortoise.move(randomNumber.nextInt(10)); /* Next move*/
			hare.move(randomNumber.nextInt(10)); /* Next move*/
			RaceDisplay raceNextTick = new RaceDisplay(tortoise.getPos(), hare.getPos()); /* Display position.*/
		}
		/* Determine who is winner and display.*/
		if(winner == 1) {
			System.out.println("TORTOISE WIN!!! YAY!!!");
		} 
		else {
			System.out.println("Hare wins. Yuch.");
		}

	}
	/* Check who is goal*/
	private int checkPos(Tortoise t, Hare h) {
		if(t.getPos() >= GOAL) { /* tortoise goal*/
			winner = 1;
			return 1;
		}
		else if (h.getPos() >= GOAL) { /* hare goal*/
			winner = -1;
			return 1;
		}
		else { /* They're not goal yet.*/
			return 0;
		}
	}
}
