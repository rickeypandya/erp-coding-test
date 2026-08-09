package com.erp.controller;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
public class InventoryController {

    private final JdbcTemplate jdbcTemplate;

    public InventoryController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    /**
     * Returns all inventory products where quantity is
     * less than or equal to the reorder level.
     */
    @GetMapping("/api/inventory/alerts")
    public List<Map<String, Object>> getAlerts() {
        String sql = """
            SELECT id, product_name, quantity, reorder_level
            FROM inventory
            WHERE quantity <= reorder_level
            """;

        return jdbcTemplate.queryForList(sql);
    }
}
