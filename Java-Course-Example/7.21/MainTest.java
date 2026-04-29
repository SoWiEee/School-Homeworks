package javaHw;

public class MainTest {
	public static void main(String[] args) {
		TurtleGraphics thisTurtle = new TurtleGraphics();
		thisTurtle.commandTable();
		System.out.println();
		thisTurtle.readCommands();
	}
}
