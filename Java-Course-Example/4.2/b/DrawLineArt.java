package javaHw;
import java.awt.Graphics;
import javax.swing.JPanel;

public class DrawLineArt extends JPanel{
	public void paintComponent(Graphics g) {
		super.paintComponent(g);
		
		int numberOfSlide = 15;
		int width = getWidth();
		int height = getHeight();
		
		for (int i = 0; i < numberOfSlide; i++) {
			g.drawLine(0, 0 + i * (height / numberOfSlide), 0 + i * (width / numberOfSlide), height);
			g.drawLine(0 + i * (width / numberOfSlide), height, width, height - i * (height / numberOfSlide));
			g.drawLine(width, height - i * (height / numberOfSlide), width - i * (width / numberOfSlide), 0);
			g.drawLine(width - i * (width / numberOfSlide), 0, 0, 0 + i * (height / numberOfSlide));
		}
	}
}
