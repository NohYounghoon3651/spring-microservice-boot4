package se.magnus.api.composite.product;

public class RecommendationSummary {

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private int recommendationId;
  private String author;
  private int rate;
  private String content;

  public RecommendationSummary() {
    this.recommendationId = 0;
    this.author = null;
    this.rate = 0;
    this.content = null;
  }

  public RecommendationSummary(int recommendationId, String author, int rate, String content) {
    this.recommendationId = recommendationId;
    this.author = author;
    this.rate = rate;
    this.content = content;
  }

  public int getRecommendationId() {
    return recommendationId;
  }

  public String getAuthor() {
    return author;
  }

  public int getRate() {
    return rate;
  }

  public String getContent() {
    return content;
  }
}
