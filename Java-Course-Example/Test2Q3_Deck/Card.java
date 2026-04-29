public class Card{
	private String suit;
	private String face;
	
	// constructor
	public Card(String f, String s) {
		this.suit = s;
		this.face = f;
	}
	
	// getter
	public String getSuit() { return suit; }
	public String getFace() { return face; }
	
	// return Card String
	public String toString() {
		return face + " of " + suit;
	}
}