package javaHw;

import java.util.Random;

public class CAIReducingStudentFatigue {
	private int answer;
	private String question;

	public boolean checkAnswer(int userAns) {
		Random randNumber = new Random();
		randNumber.setSeed(randNumber.nextInt());
		int responseNum = 0;

		responseNum = randNumber.nextInt(4) + 1;

		if (userAns == answer) {
			switch (responseNum) {
				case 1:
					System.out.println("Very good!");
					break;
				case 2:
					System.out.println("Excellent!");
					break;
				case 3:
					System.out.println("Nice work!");
					break;
				case 4:
					System.out.println("Keep up the good work!");
					break;
			}
			return true;
		} else {
			switch (responseNum) {
				case 1:
					System.out.println("No. Please try again.");
					break;
				case 2:
					System.out.println("Wrong. Try once more.");
					break;
				case 3:
					System.out.println("Don't give up!");
					break;
				case 4:
					System.out.println("No. Keep trying.");
					break;
			}
			return false;
		}
	}

	public void generateQuestion() {
		Random randNumber = new Random();
		randNumber.setSeed(randNumber.nextInt());
		int multiplicator = randNumber.nextInt(10);
		int multiplicand = randNumber.nextInt(10);

		question = String.format("How much is %d times %d?", multiplicator, multiplicand);
		answer = multiplicator * multiplicand;
	}

	public void setAnswer(int answer) {
		this.answer = answer;
	}

	public int getAnswer() {
		return this.answer;
	}

	public String getQuestion() {
		return this.question;
	}
}
