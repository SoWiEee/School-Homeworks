//DeckOfCards class represents a deck of playing cards
import java.security.SecureRandom;

public class DeckOfCards {
	//random number generator
	private static final SecureRandom randomNumbers = new SecureRandom();
	private static final int NUMBER_OF_CARDS=52;//constant of Cards
	private static final String faces[]= {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"};
	private static final String suits[]= {"Hearts", "Dimonds", "Clubs", "Spades"};

	private Card[] deck=new Card[NUMBER_OF_CARDS];//Card references
	private int currentCard=0;//index of next Card to be dealt(0-51)

	//constructor fill deck of cards
	public DeckOfCards() {
		deck=new Card[52];

		//populate deck with Card objects
		for(int count=0;count<deck.length;count++) {
			deck[count]=new Card(faces[count%13],suits[count/13]);
		}
	}


	//shuffle deck of Cards with one-pass algorithm
	public void shuffle() {
		//next call to method dealCard should start at deck[0] again
		currentCard=0;

		//random pick two card and swap them 21 times
		for(int i=0;i<21;i++){
			//select a random number between 0 and 51
			int first=randomNumbers.nextInt(NUMBER_OF_CARDS);
			int second=randomNumbers.nextInt(NUMBER_OF_CARDS);
			while(second==first){//ensure first and second card not the same card
				second=randomNumbers.nextInt(NUMBER_OF_CARDS);
			}

			//swap current Card with randomly selected Card
			Card temp=deck[first];
			deck[first]=deck[second];
			deck[second]=temp;
		}

	}


	//deal one Card
	public Card dealCard(){
		//determine whether Cards remain to be dealt
		if(currentCard<deck.length){
			return deck[currentCard++];//return current Card in array
		}
		else{
			return null;//return null to indicate that all Card were dealt
		}
	}
}
