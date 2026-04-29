package javaHw;

import java.io.PrintStream;
import java.util.Scanner;

public class TurtleGraphics {
	private final int MAXCOMMANDS = 100;
	private final int SIZE = 20;
	private int[][] floor;
	private int[][] command;
	private boolean penDown;
	private int xPos, yPos, direction;

	public TurtleGraphics() {
		floor = new int[SIZE][SIZE];
		command = new int[MAXCOMMANDS][2];
		penDown = false;
		direction = 0;
		xPos = 0;
		yPos = 0;
	}

	private void turtleDraw(boolean penCon, int[][] img, int dir, int dis) {
		int count = 0;
		switch (dir) {
			case 1: // up
				for (count = 1; count <= dis && yPos - count >= 0; ++count)
					if (penCon)
						img[yPos - count][xPos] = 1;
				yPos -= count - 1;
				break;
			case 2: // right
				for (count = 1; count <= dis && xPos + count < SIZE; ++count)
					if (penCon)
						img[yPos][xPos + count] = 1;
				xPos += count - 1;
				break;
			case 3: // down
				for (count = 1; count <= dis && yPos + count < SIZE; ++count)
					if (penCon)
						img[yPos + count][xPos] = 1;
				yPos += count - 1;
				break;
			case 4: // left
				for (count = 1; count <= dis && xPos - count >= 0; ++count)
					if (penCon)
						img[yPos][xPos - count] = 1;
				xPos -= count - 1;
				break;
		}
	}

	// up 1, right 2, down 3, left 4
	private int moveDirection(int curDir, boolean isRight) {
		if (curDir != 0) {
			if (isRight)
				curDir = (++curDir == 5) ? 1 : curDir;
			else
				curDir = (--curDir == 0) ? 4 : curDir;
		} else if (isRight)
			curDir = 2;
		else
			curDir = 4;

		return (curDir);
	}

	private void diplayDraw() {
		for (int j = 0; j < SIZE; j++) {
			for (int i = 0; i < SIZE; i++)
				System.out.print((floor[j][i] == 1) ? "*" : " ");
			System.out.println();
		}
	}

	private void executeCommand() {
		int cmd = 0, moveSpaces = 0;
		for (int i = 0; i < MAXCOMMANDS; i++) {
			cmd = command[i][0];
			if (cmd == 1)
				penDown = false;
			else if (cmd == 2)
				penDown = true;
			else if (cmd == 3)
				direction = moveDirection(direction, true);
			else if (cmd == 4)
				direction = moveDirection(direction, false);
			else if (cmd == 5) {
				moveSpaces = command[i][1];
				turtleDraw(penDown, floor, direction, moveSpaces);
			} else if (cmd == 6) {
				diplayDraw();
			} else if (cmd == 9)
				break;
		}
	}

	public void readCommands() {
		int commandNumber = 0, commandSpace = 0, count = 0;
		Scanner jin = new Scanner(System.in);
		PrintStream jout = System.out;

		jout.println("Input commands (Input 9 to quit):");
		while (count < MAXCOMMANDS) {
			commandNumber = jin.nextInt();
			command[count][0] = commandNumber;
			command[count][1] = -1;
			if (command[count][0] == 9)
				break;

			if (commandNumber == 5) {
				jout.println("Input how many spaces to move");
				commandSpace = jin.nextInt();
				command[count][1] = commandSpace;
			}
			count++;
		}
		executeCommand();
		jout.close();
		jin.close();
	}

	public void commandTable() {
		System.out.printf("%s\t%s\n", "Command", "Meaning");
		System.out.printf("%-7d\t%s\n", 1, "Pen up");
		System.out.printf("%-7d\t%s\n", 2, "Pen down");
		System.out.printf("%-7d\t%s\n", 3, "Turn right");
		System.out.printf("%-7d\t%s\n", 4, "Turn left");
		System.out.printf("%-7s\t%s\n", "5,10", "Move forward 10 spaces");
		System.out.printf("%-7d\t%s\n", 6, "Display the drawing");
		System.out.printf("%-7d\t%s\n", 9, "End to input");
	}
}
