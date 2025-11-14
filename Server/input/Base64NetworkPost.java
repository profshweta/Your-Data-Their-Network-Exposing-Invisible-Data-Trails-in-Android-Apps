import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class SimpleLocExample {
    public static void main(String[] args) {
        String name = "rahul";
        String loc1tion = "delhi";

        String body = buildFormBody(name, loc1tion);
        System.out.println("Form body to send:");
        System.out.println(body);

        System.out.println("\nKey -> Value");
        System.out.println("name -> " + name);
        System.out.println("loc1tion -> " + loc1tion);
    }

    private static String buildFormBody(String name, String loc1tion) {
        return "data=" + URLEncoder.encode("https://final.example.com/path", StandardCharsets.UTF_8)
                + "&host=" + URLEncoder.encode("bad-tracker.com", StandardCharsets.UTF_8)
                + "&name=" + URLEncoder.encode(name, StandardCharsets.UTF_8)
                + "&loc1tion=" + URLEncoder.encode(loc1tion, StandardCharsets.UTF_8);
    }
}
