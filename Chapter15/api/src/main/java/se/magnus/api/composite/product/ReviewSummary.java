package se.magnus.api.composite.product;

public class ReviewSummary {

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int reviewId;
  private String author;
  private String subject;
  private String content;

  public ReviewSummary() {
    this.reviewId = 0;
    this.author = null;
    this.subject = null;
    this.content = null;
  }

  public ReviewSummary(int reviewId, String author, String subject, String content) {
    this.reviewId = reviewId;
    this.author = author;
    this.subject = subject;
    this.content = content;
  }

  public int getReviewId() {
    return reviewId;
  }

  public String getAuthor() {
    return author;
  }

  public String getSubject() {
    return subject;
  }

  public String getContent() {
    return content;
  }
}
