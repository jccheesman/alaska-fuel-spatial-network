#!/usr/bin/env python3
"""Thin driver: hard QA gates on the built friction stack.

Calls friction_surface.qa.qa_friction_stack.main — verifies the 14-file
contract, profile conformance, ice-gating direction (Jul > Jan barge
pixels), and the overland value floor.

Run:  python workflows/01_friction_build/03_qa_friction_stack.py
"""
import sys

from friction_surface.qa.qa_friction_stack import main

if __name__ == "__main__":
    sys.exit(main())
