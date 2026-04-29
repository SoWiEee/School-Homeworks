import java.util.Scanner;

public class Main {
		public static void main(String[] args) {
	        Scanner input = new Scanner(System.in); //use scanner
	        int aGrade = 0;  
	        int bGrade = 0;
	        int cGrade = 0;
	        int dGrade = 0;

	        for (int i = 0 ; i < 5; i++){
	            System.out.println("Enter the student's name and the grade=>");
	            int student = input.nextInt();
	            char grade = input.next().charAt(0);
	            switch(grade){
	                case 'A':
	                    ++aGrade;
	                    break;
	                case 'B':
	                    ++bGrade;
	                    break;
	                case 'C':
	                    ++cGrade;
	                    break;
	                case 'D':
	                    ++dGrade;
	                    break;
	            }
	        }
	        System.out.println("There are " + aGrade + " studentS got A");
	        System.out.println("There are " + bGrade + " studentS got B");
	        System.out.println("There are " + cGrade + " studentS got C");
	        System.out.println("There are " + dGrade + " studentS got D");
	    }
}
