package javaHw;
import javax.swing.JFrame;

public class DrawLIneArtTest {
	public static void main(String[] args) {
		DrawLineArt lineArt = new DrawLineArt();
		
		JFrame application = new JFrame();
		
		application.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		
		application.add(lineArt);
		application.setSize(500, 500);
		application.setVisible(true);
	}
}
