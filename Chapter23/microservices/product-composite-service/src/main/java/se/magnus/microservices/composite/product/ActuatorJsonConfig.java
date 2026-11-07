package se.magnus.microservices.composite.product;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import org.springframework.boot.actuate.endpoint.jackson.EndpointJsonMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import tools.jackson.databind.cfg.EnumFeature;
import tools.jackson.databind.json.JsonMapper;

/**
 * Spring Boot 4 serializes actuator responses with an isolated Jackson 3 JsonMapper. Jackson 3
 * writes enums using toString() by default, which turns the Resilience4j state transition
 * CLOSED_TO_OPEN in /actuator/circuitbreakerevents into "State transition from CLOSED to OPEN".
 * This mapper keeps Spring Boot's settings for actuator responses (non-null values only) and
 * writes enums by name, as Jackson 2 did.
 */
@Configuration(proxyBeanMethods = false)
public class ActuatorJsonConfig {

  @Bean
  @Primary
  EndpointJsonMapper enumByNameEndpointJsonMapper() {
    JsonMapper jsonMapper = JsonMapper.builder()
      .changeDefaultPropertyInclusion(value -> value.withValueInclusion(Include.NON_NULL).withContentInclusion(Include.NON_NULL))
      .disable(EnumFeature.WRITE_ENUMS_USING_TO_STRING)
      .build();
    return () -> jsonMapper;
  }
}
