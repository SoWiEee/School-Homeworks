package javaHw;

import java.awt.Color;
import java.awt.Graphics;
import java.util.Random;

import javax.swing.JFrame;
import javax.swing.JPanel;

public class RandomShape extends JPanel {
	private static final int MAXWIDTH = 500;
	private static final int MAXHEIGHT = 500;
	private static final int SHAPEWIDTH = MAXWIDTH / 2;
	private static final int SHAPEHEIGHT = MAXHEIGHT / 2;

	public static void main(String[] args) {
		RandomShape shapes = new RandomShape();
		JFrame app = new JFrame();

		app.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		app.add(shapes);
		app.setSize(MAXWIDTH, MAXHEIGHT);
		app.setVisible(true);
	}

	public void paintComponent(Graphics g) {
		Random randNumber = new Random();
		randNumber.setSeed(randNumber.nextInt());
		Color randColor;

		int shapeSelected, rand_x, rand_y, rand_shape_width, rand_shape_height;

		for (int i = 0; i < 10; i++) {
			shapeSelected = randNumber.nextInt(2) + 1;
			rand_x = randNumber.nextInt(MAXWIDTH);
			rand_y = randNumber.nextInt(MAXHEIGHT);
			rand_shape_width = randNumber.nextInt(SHAPEWIDTH) + 1;
			rand_shape_height = randNumber.nextInt(SHAPEHEIGHT) + 1;
			randColor = new Color(randNumber.nextInt(256), randNumber.nextInt(256), randNumber.nextInt(256));

			if (shapeSelected == 1) {
				g.setColor(randColor);
				g.fillRect(rand_x, rand_y, rand_shape_width, rand_shape_height);
			} else {
				g.setColor(randColor);
				g.fillOval(rand_x, rand_y, rand_shape_width, rand_shape_height);
			}
		}
	}
}
