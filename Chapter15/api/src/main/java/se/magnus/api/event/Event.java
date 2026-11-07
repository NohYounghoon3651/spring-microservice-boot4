package se.magnus.api.event;

import static java.time.ZonedDateTime.now;

import java.time.ZonedDateTime;
import tools.jackson.databind.annotation.JsonSerialize;
import tools.jackson.databind.ext.javatime.ser.ZonedDateTimeSerializer;

public class Event<K, T> {

  public enum Type {
    CREATE,
    DELETE
  }

  // Fields are not final: Jackson 3 does not set final fields when deserializing
  // (MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS is disabled by default).
  private Type eventType;
  private K key;
  private T data;
  private ZonedDateTime eventCreatedAt;

  public Event() {
    this.eventType = null;
    this.key = null;
    this.data = null;
    this.eventCreatedAt = null;
  }

  public Event(Type eventType, K key, T data) {
    this.eventType = eventType;
    this.key = key;
    this.data = data;
    this.eventCreatedAt = now();
  }

  public Type getEventType() {
    return eventType;
  }

  public K getKey() {
    return key;
  }

  public T getData() {
    return data;
  }

  @JsonSerialize(using = ZonedDateTimeSerializer.class)
  public ZonedDateTime getEventCreatedAt() {
    return eventCreatedAt;
  }
}
