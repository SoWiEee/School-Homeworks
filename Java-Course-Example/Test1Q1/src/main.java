
public class main {

	public static void main(String[] args) {
		student[] students;//array to store class student
		int lowest[]=new int[3];//array to store lowest grade,[grade book, test num, student]
		int highest[]=new int[3];//array to store highest grade,[grade book, test num, student]
		int aver_count[]=new int[11];//array to store average distribution count

		students=new student[20];//new 20 student
		lowest[0]=100;//initial assume lowest=100
		highest[0]=0;//initial assume highest=100

		//initial array to store average distribution count=0
		for(int i=0;i<11;i++) {
			aver_count[i]=0;
		}
		System.out.println("Welcome to the grade book for\n"
				+ "CS101 Introduction to Java Programming\n\n"
				+ "The grades are:\n");

		System.out.println("\t\t"+"Test 1\tTest 2\tTest 3\tAverage");

		//check each student to update lowest and highest grade
		for(int i=1;i<=20;i++) {
			students[i-1]=new student();//創20個學生資料
			for(int j=0;j<3;j++) {//three test
				if(students[i-1].get_test(j)<lowest[0]) {//grade lower than lowest grade
					lowest[0]=students[i-1].get_test(j);//成績
					lowest[1]=j+1;//第幾次考試
					lowest[2]=i;//第幾個學生
				}
				if(students[i-1].get_test(j)>highest[0]) {//grade higher than lowest grade
					highest[0]=students[i-1].get_test(j);
					highest[1]=j+1;
					highest[2]=i;
				}
			}

			//calculate this student's average is in which distribution
			int a=(int)students[i-1].get_average()/10%10;
			aver_count[a]=aver_count[a]+1;

			System.out.printf("Student %d\t%d\t%d\t%d\t%.2f\n",i,students[i-1].get_test(0),students[i-1].get_test(1),students[i-1].get_test(2),students[i-1].get_average());

		}

		System.out.println();
		System.out.println("Lowest grade in the grade book is "+lowest[0]+" which is Test "+lowest[1]+" of Student "+lowest[2]);
		System.out.println("Highest grade in the grade book is "+highest[0]+" which is Test "+highest[1]+" of Student "+highest[2]);

		System.out.println();
		System.out.println("Overall average grade distribution:");
		for(int i=0;i<11;i++) {
			if(i<10) {
				System.out.print(i+"0-"+i+"9:");
			}
			else {
				System.out.println("  100:");
			}

			for(int j=0;j<aver_count[i];j++) {//print the star for the distribution
				System.out.print("*");
			}

			System.out.println();
		}
	}

}