//Card class represents a playing card
public class Card {
	private final String face;//face of card("1","2",...)
	private final String suit;//suit of card("Hearts","Diamonds",...)

	//two-argument constructor initializes card's face and suit
	public Card(String cardFace,String Cardsuit) {
		this.face=cardFace;//initialize of card
		this.suit=Cardsuit;//initialize of suit
	}

	//return String representation of Card
	public String toString() {
		return face+" of "+suit;
	}

}