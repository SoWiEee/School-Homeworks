import java.security.*;
import java.util.HashMap;

/* Important Function
 * put(key, value) => 新增元素
 * size() => hashMap 的長度
 * getOrDefault(card.getFace(), 0) => 取值否則回傳 0
 * containsValue(4) => 是否包含 value = 4
 */

public class DeckOfCards{
	private static final SecureRandom randomNumbers = new SecureRandom();
	private static final String faces[]= {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"};
	private static final String suits[]= {"Hearts", "Diamonds", "Clubs", "Spades"};
	
	// 建立牌組
	private Card[] deck;
	private int currentCard;
	
	// constructor
	public DeckOfCards() {
		deck = new Card[52];

		// 牌面初始化
		for(int i = 0; i < deck.length; i++) {
			deck[i] = new Card(faces[i%13], suits[i/13]);
		}
	}
	
	// shuffle
	public void shuffle() {
        currentCard = 0;
        // 每張牌隨機找另一張互換
        for (int first = 0; first < deck.length; first++) {
            int second = randomNumbers.nextInt(52);	// 0~51
            Card temp = deck[first];
            deck[first] = deck[second];
            deck[second] = temp;
        }
    }
	
	// deal 1 card
    public Card dealCard() {
    // 確定是否仍有待發牌
        if(currentCard < deck.length) {
            return deck[currentCard++];	// 回傳那張牌
        }else{
            return null;
        }
    }
	
 // check combination
    public int check(Card[] hand) {
    	// HashMap <key, value>
    	HashMap<String, Integer> faceCount = new HashMap<>();	// 每種數字的次數
    	HashMap<String, Integer> suitCount = new HashMap<>();	// 每種花色的次數

    	// card table
        for (Card card : hand) {
        	// 把 face/suit 對應的 count++，若 face/suit 不存在，則 count=0 +1
            faceCount.put(card.getFace(), faceCount.getOrDefault(card.getFace(), 0) + 1);
            suitCount.put(card.getSuit(), suitCount.getOrDefault(card.getSuit(), 0) + 1);
        }

        boolean isFlush = suitCount.size() == 1;	// 同花
        boolean isStraight = straight(hand);	// 順子

        if (isFlush && isStraight) return 8; // 同花順
        if (faceCount.containsValue(4)) return 7; // 鐵支 (4 face)
        if (faceCount.containsValue(3) && faceCount.containsValue(2)) return 6; // 葫蘆
        if (isFlush) return 5;
        if (isStraight) return 4;
        if (faceCount.containsValue(3)) return 3; // 三條
        if (faceCount.size() == 3) return 2; // Two Pairs
        if (faceCount.size() == 4) return 1; // One Pair

        return 0; // No combination
    }

    // 檢查有沒有順子
    private boolean straight(Card[] hand) {
    	// 記錄每張牌的 face
        int[] faceValues = new int[hand.length];
        // 把 face 轉成數字儲存起來
        for (int i = 0; i < hand.length; i++) {
            faceValues[i] = getFaceValue(hand[i].getFace());
        }
        // 排序陣列
        java.util.Arrays.sort(faceValues);
        // 檢查當前數字是否比前一個數字大 1
        for (int i = 1; i < faceValues.length; i++) {
            if (faceValues[i] != faceValues[i - 1] + 1) {
                return false;
            }
        }
        return true;
    }
	
    private int getFaceValue(String face) {
		switch (face) {
			case "1": return 1;
			case "2": return 2;
			case "3": return 3;
			case "4": return 4;
			case "5": return 5;
			case "6": return 6;
			case "7": return 7;
			case "8": return 8;
			case "9": return 9;
			case "10": return 10;
			case "J": return 11;
			case "Q": return 12;
			case "K": return 13;
			default: throw new IllegalArgumentException("Invalid face value");
		}
	}
	
}