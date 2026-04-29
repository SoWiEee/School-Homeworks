package javaHw;

import java.io.PrintStream;
import java.util.Scanner;

public class MainTest {
	public static void main(String[] args) {
		CAIReducingStudentFatigue test = new CAIReducingStudentFatigue();
		Scanner jin = new Scanner(System.in);
		PrintStream jout = System.out;
		boolean isQuit = false, nonAnswer = false, checkQuit;
		String quitSentinel;

		while (!isQuit) {
			test.generateQuestion();
			jout.printf("Question: %s\n", test.getQuestion());

			jout.println("Input your answer: ");
			nonAnswer = false;
			while (!nonAnswer) {
				nonAnswer = test.checkAnswer(jin.nextInt());
			}

			jout.println("\nQuit this program input y:");
			quitSentinel = jin.next();
			checkQuit = quitSentinel.equals("Y") || quitSentinel.equals("y");
			if (checkQuit) {
				isQuit = true;
			}
		}

		jin.close();
	}
}
