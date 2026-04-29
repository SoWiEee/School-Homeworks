import java.util.Scanner;

public class DeckOfCardsTest{
	public static void main(String[] args) {
		Scanner input = new Scanner(System.in);
		
		while(true){
			System.out.println("========= New Game =========");
			// 初始化牌組並洗牌
			DeckOfCards myDeck = new DeckOfCards();
			myDeck.shuffle();
			
			// 創建手牌
			Card[] hand1 = new Card[5];
			Card[] hand2 = new Card[5];
			
			// 發牌並顯示
			System.out.print("[*] Hand 1: ");
			for(int i = 0; i < 5; i++) {
				Card dealHand1 = myDeck.dealCard();
				hand1[i] = dealHand1;
				System.out.print(dealHand1 + "\t");
			}
			System.out.println();
			
			System.out.print("[*] Hand 2: ");
			for(int i = 0; i < 5; i++) {
				Card dealHand2 = myDeck.dealCard();
				hand2[i] = dealHand2;
				System.out.print(dealHand2 + "\t");
			}
			System.out.println();
			
			// check combination and winner
			if(myDeck.check(hand1) < myDeck.check(hand2)){
				System.out.println("[*] Hand 1 win!!");
			}
			else if(myDeck.check(hand1) > myDeck.check(hand2)){
				System.out.println("[*] Hand 2 win!!");
			}
			else{
				System.out.println("[*] Tie!!");
			}
			
			// continue
			System.out.print("Continue game?(y/n): ");
			String conti = input.next();
			if(conti.equals("n")){
				System.out.print("[V] Game End...\n");
				break;
			}
			System.out.println();
		}
		input.close();	// 注意要關掉！
	}
}