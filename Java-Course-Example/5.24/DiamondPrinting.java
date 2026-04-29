package javaHw;

import java.io.PrintStream;

public class DiamondPrinting {
	public static void main(String[] args) {
		int size = 9, row, col, mid;
		PrintStream jout = System.out;
		
		if (size % 2 == 1) {
			mid = (int)(size / 2) + 1;
			
			for (row = 1; row <= size; row++) {
				for (col = mid - row; col > 0; col--)
					jout.print(" ");
				for (col = row - mid; col > 0; col--)
					jout.print(" ");
				for (col = 1; col <= 1 + 2 * (row - 1) && row <= mid; col++)
					jout.print("*");
				for (col = 1; col <= 1 + 2 * (size - row) && row > mid; col++)
					jout.print("*");
				jout.println();
			}
		}
	}
}
