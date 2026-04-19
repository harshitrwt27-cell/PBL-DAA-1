#!/usr/bin/env python3
"""
Bus Route Optimization Demo - Multi-Region
Demonstrates the Dijkstra and A* algorithms across multiple regions
"""

from app import dijkstra, a_star, build_region_graph, REGIONS

def demo_region(region_name):
    print(f"\n{'='*60}")
    print(f"🚍 {REGIONS[region_name]['name'].upper()} DEMO")
    print(f"{'='*60}")
    
    graph, coordinates = build_region_graph(region_name)
    stops = sorted(list(graph.keys()))
    
    print(f"Total bus stops: {len(graph)}")
    print(f"Sample stops: {stops[:3]}")
    
    if len(stops) >= 2:
        # Test with first and last stops
        start = stops[0]
        end = stops[-1]
        
        print(f"\n📍 Route: {start} → {end}")
        print("-" * 50)
        
        # Dijkstra
        d_cost, d_path = dijkstra(graph, start, end)
        if d_cost != float("inf"):
            print(f"Dijkstra: {d_cost} km ({len(d_path)} stops)")
            print(f"Path: {' → '.join([s.split(': ')[0] for s in d_path])}")
        else:
            print("Dijkstra: No route found")
        
        # A*
        a_cost, a_path = a_star(graph, start, end, coordinates)
        if a_cost != float("inf"):
            print(f"A*:       {a_cost} km ({len(a_path)} stops)")
            print(f"Path: {' → '.join([s.split(': ')[0] for s in a_path])}")
        else:
            print("A*: No route found")
        
        # Comparison
        if d_cost == a_cost and d_cost != float("inf"):
            print("✅ Both algorithms found same optimal route")
        elif d_cost != float("inf") and a_cost != float("inf"):
            print("⚠️  Different distances found")

def main():
    print("\n" + "="*60)
    print("🚌 MULTI-REGION BUS ROUTE OPTIMIZATION SYSTEM")
    print("="*60)
    
    # Demo all regions
    for region in REGIONS.keys():
        demo_region(region)
    
    print("\n" + "="*60)
    print("✅ All demos completed successfully!")
    print("="*60)
    print("\n💡 To run the web app, use: python app.py")

if __name__ == "__main__":
    main()