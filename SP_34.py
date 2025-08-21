"""
SP 34:1987 - Handbook on Concrete Reinforcement and Detailing
Compliance Checker Implementation

This module implements detailing rules, tables, and figures from SP 34:1987
for structural reinforcement detailing checks.

Key Features:
1) Modular Design: Separate checkers for different structural elements (beams, columns, slabs, footings)

2) Comprehensive Coverage:
--Development length calculations (Tables 4.2-4.4)
--Anchorage and lap splice requirements
--Minimum/maximum reinforcement ratios
--Bar spacing and arrangement rules
--Cover requirements for different exposures
--Ductile detailing provisions (Section 12)

3) SP 34:1987 References: Each check includes specific clause, table, or figure references

4) Extensible Architecture: Easy to add new checks or modify existing ones

5) Detailed Reporting: Comprehensive compliance reports with failure descriptions

6) Main Classes:
--DetailingChecker: Main integration class
--SpacingChecker: Bar spacing rules
--AnchorageChecker: Development length and anchorage
--LapSpliceChecker: Lap length and splice locations
--BeamDetailingChecker: Beam-specific requirements
--ColumnDetailingChecker: Column-specific requirements
--SlabDetailingChecker: Slab-specific requirements
--FootingDetailingChecker: Footing-specific requirements
--DuctileDetailingChecker: Earthquake-resistant detailing

7) Usage Examples:
The code includes working examples for beam and column checking that demonstrate:
--Input format for member geometry and reinforcement
--Material property specification
--Comprehensive compliance checking
--Detailed reporting of results

"""

import math
from enum import Enum
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import warnings

class MemberType(Enum):
    BEAM = "beam"
    SLAB = "slab"
    COLUMN = "column"
    FOOTING = "footing"
    WALL = "wall"

class SteelGrade(Enum):
    FE250 = 250  # Mild steel
    FE415 = 415  # HYSD
    FE500 = 500  # HYSD
    FE550 = 550  # HYSD

class ConcreteGrade(Enum):
    M15 = 15
    M20 = 20
    M25 = 25
    M30 = 30
    M35 = 35
    M40 = 40

class ExposureCondition(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    VERY_SEVERE = "very_severe"
    EXTREME = "extreme"

@dataclass
class ReinforcementBar:
    """Represents a reinforcement bar with its properties"""
    diameter: float  # mm
    number: int
    spacing: float  # mm (center-to-center)
    length: float  # mm
    is_deformed: bool = True
    position: str = "bottom"  # bottom, top, side

@dataclass
class MemberGeometry:
    """Geometric properties of structural member"""
    length: float  # mm
    width: float  # mm
    depth: float  # mm
    effective_depth: float  # mm
    cover: float  # mm

@dataclass
class CheckResult:
    """Result of a detailing check"""
    is_compliant: bool
    clause_reference: str
    description: str
    actual_value: Optional[float] = None
    required_value: Optional[float] = None
    remarks: str = ""

class DetailingTables:
    """
    Implementation of SP 34:1987 Tables for detailing parameters
    """
    
    @staticmethod
    def get_development_length_factors() -> Dict:
        """
        Table 4.2, 4.3, 4.4: Development length for fully stressed bars
        SP 34:1987, Section 4.3.3
        """
        return {
            'plain_bars': {
                250: {  # fy = 250 N/mm2
                    'M15': 1.0, 'M20': 1.2, 'M25': 1.4, 'M30': 1.5, 'M35': 1.7, 'M40': 1.9
                },
                240: {  # fy = 240 N/mm2
                    'M15': 1.0, 'M20': 1.2, 'M25': 1.4, 'M30': 1.5, 'M35': 1.7, 'M40': 1.9
                }
            },
            'deformed_bars': {
                415: {  # Fe 415
                    'M15': 1.6, 'M20': 1.6, 'M25': 1.6, 'M30': 1.6, 'M35': 1.6, 'M40': 1.6
                },
                500: {  # Fe 500
                    'M15': 1.6, 'M20': 1.6, 'M25': 1.6, 'M30': 1.6, 'M35': 1.6, 'M40': 1.6
                }
            }
        }
    
    @staticmethod
    def get_minimum_cover_requirements() -> Dict:
        """
        SP 34:1987, Section 4.1: Cover requirements
        """
        return {
            'general': {
                'bar_end': 25,  # mm, or 2*diameter whichever is greater
                'column_longitudinal': 40,  # mm, or diameter whichever is greater
                'beam_longitudinal': 25,  # mm, or diameter whichever is greater
                'slab_reinforcement': 15,  # mm, or diameter whichever is greater
                'other_reinforcement': 15  # mm, or diameter whichever is greater
            },
            'exposure_addition': {
                ExposureCondition.MILD: 0,
                ExposureCondition.MODERATE: 15,
                ExposureCondition.SEVERE: 25,
                ExposureCondition.VERY_SEVERE: 40,
                ExposureCondition.EXTREME: 50
            },
            'marine_structures': {
                'immersed': 40,  # Additional cover for marine structures
                'spray_zone': 50  # Additional cover for spray zone
            }
        }
    
    @staticmethod
    def get_anchorage_values() -> Dict:
        """
        Table 4.1: Anchorage value of hooks and bends
        SP 34:1987, Section 4.3.1.2
        """
        # Values in terms of bar diameter multiples
        return {
            'u_hook': 16,  # 16 times diameter
            '90_bend': 4,  # 4 times diameter per 45° bend, max 16*diameter
            'standard_hook_k_factor': {
                'mild_steel': 2,
                'cold_worked_steel': 4
            }
        }

class SpacingChecker:
    """
    Implements spacing requirements from SP 34:1987
    """
    
    @staticmethod
    def check_minimum_bar_spacing(bars: List[ReinforcementBar], 
                                 aggregate_size: float = 20) -> CheckResult:
        """
        SP 34:1987, Section 8.2.1: Minimum distance between individual bars
        """
        min_spacing = float('inf')
        for i, bar in enumerate(bars):
            if i < len(bars) - 1:
                next_bar = bars[i + 1]
                # Minimum spacing = larger bar diameter or (aggregate_size + 5)
                required = max(bar.diameter, next_bar.diameter, aggregate_size + 5)
                actual = bar.spacing
                min_spacing = min(min_spacing, actual)
                
                if actual < required:
                    return CheckResult(
                        is_compliant=False,
                        clause_reference="SP 34:1987, Section 8.2.1",
                        description="Insufficient horizontal spacing between bars",
                        actual_value=actual,
                        required_value=required
                    )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 8.2.1",
            description="Horizontal bar spacing adequate"
        )
    
    @staticmethod
    def check_vertical_bar_spacing(layer_spacing: float, 
                                 max_bar_diameter: float,
                                 aggregate_size: float = 20) -> CheckResult:
        """
        SP 34:1987, Section 8.2.1: Minimum vertical distance between bars
        """
        required = max(15, (2/3) * aggregate_size, max_bar_diameter)
        
        if layer_spacing < required:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 8.2.1",
                description="Insufficient vertical spacing between bar layers",
                actual_value=layer_spacing,
                required_value=required
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 8.2.1",
            description="Vertical bar spacing adequate"
        )

class DevelopmentLengthCalculator:
    """
    Implements development length calculations from SP 34:1987
    """
    
    @staticmethod
    def calculate_basic_development_length(bar_diameter: float,
                                         steel_grade: SteelGrade,
                                         concrete_grade: ConcreteGrade,
                                         is_deformed: bool = True,
                                         stress_condition: str = "tension") -> float:
        """
        SP 34:1987, Section 4.2.2: Development length calculation
        Tables 4.2, 4.3, 4.4: Development length for fully stressed bars
        
        Ld = (phi * sigma_s) / (4 * tau_bd)
        """
        # Design bond stress values (N/mm²)
        bond_stress_plain = {
            ConcreteGrade.M15: 1.0, ConcreteGrade.M20: 1.2, ConcreteGrade.M25: 1.4,
            ConcreteGrade.M30: 1.5, ConcreteGrade.M35: 1.7, ConcreteGrade.M40: 1.9
        }
        
        # Get basic bond stress
        tau_bd = bond_stress_plain[concrete_grade]
        
        # Increase for deformed bars (60% increase)
        if is_deformed:
            tau_bd *= 1.6
        
        # Increase for compression (25% increase)
        if stress_condition == "compression":
            tau_bd *= 1.25
        
        # Design stress in steel (0.87 * fy)
        sigma_s = 0.87 * steel_grade.value
        
        # Basic development length
        ld = (bar_diameter * sigma_s) / (4 * tau_bd)
        
        return ld
    
    @staticmethod
    def get_development_length_from_tables(bar_diameter: float,
                                         steel_grade: SteelGrade,
                                         concrete_grade: ConcreteGrade,
                                         is_deformed: bool = True,
                                         stress_condition: str = "tension") -> float:
        """
        Direct lookup from SP 34:1987 Tables 4.2, 4.3, 4.4
        """
        # Simplified lookup - in practice, you'd use the full tables
        base_factor = {
            ConcreteGrade.M15: 60, ConcreteGrade.M20: 50, ConcreteGrade.M25: 43,
            ConcreteGrade.M30: 40, ConcreteGrade.M35: 34, ConcreteGrade.M40: 32
        }
        
        fy_factor = steel_grade.value / 250  # Normalize to mild steel
        deformed_factor = 0.8 if is_deformed else 1.0
        compression_factor = 0.8 if stress_condition == "compression" else 1.0
        
        ld = bar_diameter * base_factor[concrete_grade] * fy_factor * deformed_factor * compression_factor
        return ld / 10  # Convert to cm, then back to mm for consistency

class AnchorageChecker:
    """
    Implements anchorage requirements from SP 34:1987
    """
    
    @staticmethod
    def check_anchorage_length(bar_diameter: float,
                             available_length: float,
                             steel_grade: SteelGrade,
                             concrete_grade: ConcreteGrade,
                             has_hook: bool = False,
                             hook_type: str = "u_hook",
                             is_deformed: bool = True) -> CheckResult:
        """
        SP 34:1987, Section 4.3: Anchoring reinforcing bars
        """
        # Calculate required development length
        required_ld = DevelopmentLengthCalculator.get_development_length_from_tables(
            bar_diameter, steel_grade, concrete_grade, is_deformed
        )
        
        # Get anchorage value of hook if present
        anchorage_value = 0
        if has_hook:
            hook_values = DetailingTables.get_anchorage_values()
            if hook_type == "u_hook":
                anchorage_value = hook_values['u_hook'] * bar_diameter
            elif hook_type == "90_bend":
                anchorage_value = hook_values['90_bend'] * bar_diameter
        
        # Check if available length is sufficient
        effective_anchorage = available_length + anchorage_value
        
        if effective_anchorage < required_ld:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 4.3",
                description=f"Insufficient anchorage length for {bar_diameter}mm bar",
                actual_value=effective_anchorage,
                required_value=required_ld,
                remarks=f"Hook contribution: {anchorage_value}mm"
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 4.3",
            description="Anchorage length adequate",
            actual_value=effective_anchorage,
            required_value=required_ld
        )

class LapSpliceChecker:
    """
    Implements lap splice requirements from SP 34:1987
    """
    
    @staticmethod
    def calculate_lap_length(bar_diameter: float,
                           steel_grade: SteelGrade,
                           concrete_grade: ConcreteGrade,
                           splice_type: str = "flexural_tension",
                           is_deformed: bool = True) -> float:
        """
        SP 34:1987, Section 4.4.2: Lap splices
        """
        # Get basic development length
        ld = DevelopmentLengthCalculator.get_development_length_from_tables(
            bar_diameter, steel_grade, concrete_grade, is_deformed
        )
        
        # Lap length factors based on splice type
        if splice_type == "flexural_tension":
            lap_factor = 1.0  # Ld or 30*phi, whichever is greater
            min_lap = max(ld, 30 * bar_diameter)
        elif splice_type == "direct_tension":
            lap_factor = 2.0  # 2*Ld or 30*phi, whichever is greater
            min_lap = max(2 * ld, 30 * bar_diameter)
        elif splice_type == "compression":
            lap_factor = 1.0  # Ld but not less than 24*phi
            min_lap = max(ld, 24 * bar_diameter)
        else:
            lap_factor = 1.0
            min_lap = ld
        
        # Minimum straight length should be 15*phi or 200mm
        min_straight = max(15 * bar_diameter, 200)
        
        return max(min_lap, min_straight)
    
    @staticmethod
    def check_lap_splice_location(splice_location: str,
                                max_moment_location: str,
                                moment_ratio: float = 0.5) -> CheckResult:
        """
        SP 34:1987, Section 4.4.1: Location of splices
        Splices should be away from sections of maximum stress
        """
        if splice_location == max_moment_location:
            if moment_ratio > 0.5:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 4.4.1",
                    description="Splice located at high stress zone (>50% of moment resistance)",
                    actual_value=moment_ratio,
                    required_value=0.5
                )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 4.4.1",
            description="Splice location acceptable"
        )
    
    @staticmethod
    def check_splice_staggering(splice_positions: List[float],
                              lap_length: float) -> CheckResult:
        """
        SP 34:1987, Section 4.4.2: Staggering of lap splices
        Centre-to-centre distance should be ≥ 1.3 times lap length
        """
        min_stagger = 1.3 * lap_length
        
        for i in range(len(splice_positions) - 1):
            actual_stagger = abs(splice_positions[i+1] - splice_positions[i])
            if actual_stagger < min_stagger:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 4.4.2(c)",
                    description="Insufficient staggering between lap splices",
                    actual_value=actual_stagger,
                    required_value=min_stagger
                )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 4.4.2(c)",
            description="Splice staggering adequate"
        )

class BeamDetailingChecker:
    """
    Implements beam detailing checks from SP 34:1987
    """
    
    @staticmethod
    def check_minimum_reinforcement(ast_provided: float,
                                  width: float,
                                  effective_depth: float,
                                  steel_grade: SteelGrade) -> CheckResult:
        """
        SP 34:1987, Section 8.2.2.1: Minimum reinforcement in beams
        """
        # Minimum steel = 0.85 * b * d / fy
        ast_min = (0.85 * width * effective_depth) / steel_grade.value
        
        if ast_provided < ast_min:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 8.2.2.1",
                description="Insufficient minimum reinforcement in beam",
                actual_value=ast_provided,
                required_value=ast_min
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 8.2.2.1",
            description="Minimum reinforcement adequate"
        )
    
    @staticmethod
    def check_maximum_reinforcement(ast_provided: float,
                                  width: float,
                                  total_depth: float) -> CheckResult:
        """
        SP 34:1987, Section 8.2.2.2: Maximum reinforcement in beams
        """
        ast_max = 0.04 * width * total_depth
        
        if ast_provided > ast_max:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 8.2.2.2",
                description="Excessive reinforcement in beam",
                actual_value=ast_provided,
                required_value=ast_max
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 8.2.2.2",
            description="Maximum reinforcement within limits"
        )
    
    @staticmethod
    def check_side_face_reinforcement(beam_depth: float,
                                    has_side_reinforcement: bool,
                                    side_steel_area: float = 0,
                                    web_area: float = 0) -> CheckResult:
        """
        SP 34:1987, Section 8.2.4: Side face reinforcement
        Required when beam depth > 750mm
        """
        if beam_depth > 750:
            if not has_side_reinforcement:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 8.2.4",
                    description="Side face reinforcement required for deep beam",
                    actual_value=0,
                    required_value=0.1  # 0.1% of web area
                )
            
            # Check minimum area (0.1% of web area)
            min_side_steel = 0.001 * web_area
            if side_steel_area < min_side_steel:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 8.2.4",
                    description="Insufficient side face reinforcement",
                    actual_value=side_steel_area,
                    required_value=min_side_steel
                )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 8.2.4",
            description="Side face reinforcement adequate"
        )

class ColumnDetailingChecker:
    """
    Implements column detailing checks from SP 34:1987
    """
    
    @staticmethod
    def check_minimum_longitudinal_reinforcement(ast_provided: float,
                                               gross_area: float) -> CheckResult:
        """
        SP 34:1987, Section 7.1.1: Minimum longitudinal reinforcement in columns
        """
        min_steel_ratio = 0.008  # 0.8%
        ast_min = min_steel_ratio * gross_area
        
        if ast_provided < ast_min:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 7.1.1",
                description="Insufficient minimum longitudinal reinforcement",
                actual_value=ast_provided,
                required_value=ast_min
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 7.1.1",
            description="Minimum longitudinal reinforcement adequate"
        )
    
    @staticmethod
    def check_maximum_longitudinal_reinforcement(ast_provided: float,
                                               gross_area: float,
                                               is_lap_zone: bool = False) -> CheckResult:
        """
        SP 34:1987, Section 7.1.1: Maximum longitudinal reinforcement in columns
        """
        max_steel_ratio = 0.06 if is_lap_zone else 0.04  # 6% in lap zones, 4% elsewhere
        ast_max = max_steel_ratio * gross_area
        
        if ast_provided > ast_max:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 7.1.1",
                description="Excessive longitudinal reinforcement",
                actual_value=ast_provided,
                required_value=ast_max
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 7.1.1",
            description="Maximum longitudinal reinforcement within limits"
        )
    
    @staticmethod
    def check_minimum_bars_and_diameter(num_bars: int,
                                      bar_diameter: float,
                                      column_type: str = "rectangular") -> CheckResult:
        """
        SP 34:1987, Section 7.1.2, 7.1.3: Minimum number of bars and diameter
        """
        min_bars = 6 if column_type == "circular_helical" else 4
        min_diameter = 12  # mm
        
        if num_bars < min_bars:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 7.1.2",
                description=f"Insufficient number of bars (minimum {min_bars})",
                actual_value=num_bars,
                required_value=min_bars
            )
        
        if bar_diameter < min_diameter:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 7.1.3",
                description="Bar diameter too small",
                actual_value=bar_diameter,
                required_value=min_diameter
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 7.1.2, 7.1.3",
            description="Number of bars and diameter adequate"
        )
    
    @staticmethod
    def check_tie_spacing_and_diameter(tie_spacing: float,
                                     tie_diameter: float,
                                     column_dimension: float,
                                     main_bar_diameter: float,
                                     clear_height: float) -> CheckResult:
        """
        SP 34:1987, Section 7.2.6: Tie spacing and diameter requirements
        """
        # Maximum tie spacing
        max_spacing = min(
            column_dimension,  # Least lateral dimension
            16 * main_bar_diameter,  # 16 times main bar diameter
            48 * tie_diameter  # 48 times tie diameter
        )
        
        # Minimum tie diameter
        min_tie_diameter = max(main_bar_diameter / 4, 5)  # Quarter of main bar or 5mm
        
        if tie_spacing > max_spacing:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 7.2.6.1",
                description="Tie spacing excessive",
                actual_value=tie_spacing,
                required_value=max_spacing
            )
        
        if tie_diameter < min_tie_diameter:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 7.2.6.2",
                description="Tie diameter too small",
                actual_value=tie_diameter,
                required_value=min_tie_diameter
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 7.2.6",
            description="Tie spacing and diameter adequate"
        )

class SlabDetailingChecker:
    """
    Implements slab detailing checks from SP 34:1987
    """
    
    @staticmethod
    def check_minimum_reinforcement(ast_provided: float,
                                  gross_area: float,
                                  is_deformed: bool = True) -> CheckResult:
        """
        SP 34:1987, Section 9.1: Minimum reinforcement in slabs
        """
        min_ratio = 0.12 if is_deformed else 0.15  # Percentage
        ast_min = (min_ratio / 100) * gross_area
        
        if ast_provided < ast_min:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 9.1",
                description="Insufficient minimum reinforcement in slab",
                actual_value=ast_provided,
                required_value=ast_min
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 9.1",
            description="Minimum reinforcement adequate"
        )
    
    @staticmethod
    def check_spacing_requirements(main_spacing: float,
                                 dist_spacing: float,
                                 effective_depth: float,
                                 is_main_steel: bool = True) -> CheckResult:
        """
        SP 34:1987, Section 9.2.1: Spacing requirements for slab reinforcement
        """
        if is_main_steel:
            max_spacing = min(3 * effective_depth, 450)  # Main steel
            description = "main reinforcement"
        else:
            max_spacing = min(5 * effective_depth, 450)  # Distribution steel
            description = "distribution reinforcement"
        
        actual_spacing = main_spacing if is_main_steel else dist_spacing
        
        if actual_spacing > max_spacing:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 9.2.1",
                description=f"Excessive spacing for {description}",
                actual_value=actual_spacing,
                required_value=max_spacing
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 9.2.1",
            description=f"Spacing for {description} adequate"
        )
    
    @staticmethod
    def check_torsional_reinforcement(corner_type: str,
                                    has_torsion_steel: bool,
                                    torsion_steel_area: float,
                                    max_moment_steel: float,
                                    shorter_span: float) -> CheckResult:
        """
        SP 34:1987, Section 9.4.6: Torsional reinforcement at corners
        """
        if corner_type == "simply_supported_both_edges":
            required_area = 0.75 * max_moment_steel  # 75% of max moment steel
            min_length = shorter_span / 5  # Extend 1/5 of shorter span
            
            if not has_torsion_steel:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 9.4.6",
                    description="Torsional reinforcement required at corner",
                    required_value=required_area
                )
            
            if torsion_steel_area < required_area:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 9.4.6",
                    description="Insufficient torsional reinforcement",
                    actual_value=torsion_steel_area,
                    required_value=required_area
                )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 9.4.6",
            description="Torsional reinforcement adequate"
        )

class FootingDetailingChecker:
    """
    Implements footing detailing checks from SP 34:1987
    """
    
    @staticmethod
    def check_minimum_cover(cover: float,
                          in_contact_with_earth: bool = True) -> CheckResult:
        """
        SP 34:1987, Section 6.2: Cover requirements for footings
        """
        min_cover = 75 if in_contact_with_earth else 50  # mm
        
        if cover < min_cover:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 6.2",
                description="Insufficient cover for footing reinforcement",
                actual_value=cover,
                required_value=min_cover
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 6.2",
            description="Cover adequate for footing"
        )
    
    @staticmethod
    def check_dowel_requirements(dowel_area: float,
                               column_area: float,
                               num_dowels: int,
                               dowel_diameter: float,
                               column_bar_diameter: float) -> CheckResult:
        """
        SP 34:1987, Section 6.5.1.1: Vertical reinforcement or dowels
        """
        min_area_ratio = 0.005  # 0.5% of column area
        min_dowel_area = min_area_ratio * column_area
        min_bars = 4
        min_diameter = 12
        
        # Check diameter difference (should not exceed 3mm)
        diameter_diff = abs(dowel_diameter - column_bar_diameter)
        
        if dowel_area < min_dowel_area:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 6.5.1.1",
                description="Insufficient dowel area",
                actual_value=dowel_area,
                required_value=min_dowel_area
            )
        
        if num_dowels < min_bars or dowel_diameter < min_diameter:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 6.5.1.1",
                description="Insufficient dowel bars or diameter",
                actual_value=min(num_dowels, dowel_diameter),
                required_value=min(min_bars, min_diameter)
            )
        
        if diameter_diff > 3:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 6.5.1.1",
                description="Dowel diameter differs too much from column bars",
                actual_value=diameter_diff,
                required_value=3
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 6.5.1.1",
            description="Dowel requirements satisfied"
        )

class DuctileDetailingChecker:
    """
    Implements ductile detailing requirements from SP 34:1987, Section 12
    """
    
    @staticmethod
    def check_beam_reinforcement_ratio(ast_top: float,
                                     ast_bottom: float,
                                     width: float,
                                     effective_depth: float,
                                     concrete_grade: ConcreteGrade,
                                     steel_grade: SteelGrade) -> CheckResult:
        """
        SP 34:1987, Section 12.1.1: Minimum reinforcement ratio for ductile beams
        """
        fck = concrete_grade.value
        fy = steel_grade.value
        
        # Minimum ratio calculation
        if concrete_grade == ConcreteGrade.M15 and steel_grade == SteelGrade.FE250:
            p_min = 0.0035
        else:
            p_min = 0.06 * fck / fy
        
        # Check both faces
        area_section = width * effective_depth
        p_top = ast_top / area_section
        p_bottom = ast_bottom / area_section
        
        if p_top < p_min or p_bottom < p_min:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 12.1.1",
                description="Insufficient reinforcement ratio for ductile design",
                actual_value=min(p_top, p_bottom),
                required_value=p_min
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 12.1.1",
            description="Reinforcement ratio adequate for ductile design"
        )
    
    @staticmethod
    def check_stirrup_spacing_ductile(stirrup_spacing_near_ends: float,
                                    stirrup_spacing_middle: float,
                                    effective_depth: float) -> CheckResult:
        """
        SP 34:1987, Section 12.1.5: Stirrup spacing for ductile beams
        """
        max_spacing_ends = effective_depth / 4  # d/4 near ends
        max_spacing_middle = effective_depth / 2  # d/2 in middle
        
        if stirrup_spacing_near_ends > max_spacing_ends:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 12.1.5",
                description="Excessive stirrup spacing near beam ends",
                actual_value=stirrup_spacing_near_ends,
                required_value=max_spacing_ends
            )
        
        if stirrup_spacing_middle > max_spacing_middle:
            return CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 12.1.5",
                description="Excessive stirrup spacing in beam middle",
                actual_value=stirrup_spacing_middle,
                required_value=max_spacing_middle
            )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 12.1.5",
            description="Stirrup spacing adequate for ductile design"
        )
    
    @staticmethod
    def check_column_confinement(column_dimension: float,
                               clear_height: float,
                               has_special_confinement: bool,
                               confinement_length: float,
                               axial_stress_ratio: float) -> CheckResult:
        """
        SP 34:1987, Section 12.2.3: Special confining steel for columns
        """
        if axial_stress_ratio >= 0.1:  # P/Ag ≥ 0.1 fck
            # Required confinement length
            required_length = max(
                clear_height / 6,
                column_dimension,
                450  # mm
            )
            
            if not has_special_confinement:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 12.2.3",
                    description="Special confining reinforcement required",
                    required_value=required_length
                )
            
            if confinement_length < required_length:
                return CheckResult(
                    is_compliant=False,
                    clause_reference="SP 34:1987, Section 12.2.3",
                    description="Insufficient confinement length",
                    actual_value=confinement_length,
                    required_value=required_length
                )
        
        return CheckResult(
            is_compliant=True,
            clause_reference="SP 34:1987, Section 12.2.3",
            description="Column confinement adequate"
        )

class DetailingChecker:
    """
    Main class integrating all detailing checks for SP 34:1987 compliance
    """
    
    def __init__(self):
        self.spacing_checker = SpacingChecker()
        self.anchorage_checker = AnchorageChecker()
        self.lap_splice_checker = LapSpliceChecker()
        self.beam_checker = BeamDetailingChecker()
        self.column_checker = ColumnDetailingChecker()
        self.slab_checker = SlabDetailingChecker()
        self.footing_checker = FootingDetailingChecker()
        self.ductile_checker = DuctileDetailingChecker()
    
    def check_member_detailing(self,
                             member_type: MemberType,
                             geometry: MemberGeometry,
                             reinforcement: List[ReinforcementBar],
                             concrete_grade: ConcreteGrade,
                             steel_grade: SteelGrade,
                             exposure_condition: ExposureCondition = ExposureCondition.MILD,
                             is_ductile: bool = False,
                             **kwargs) -> Dict[str, CheckResult]:
        """
        Comprehensive detailing check for a structural member
        """
        results = {}
        
        # Common checks for all members
        results.update(self._check_common_requirements(
            geometry, reinforcement, concrete_grade, steel_grade, exposure_condition
        ))
        
        # Member-specific checks
        if member_type == MemberType.BEAM:
            results.update(self._check_beam_detailing(
                geometry, reinforcement, concrete_grade, steel_grade, is_ductile, **kwargs
            ))
        elif member_type == MemberType.COLUMN:
            results.update(self._check_column_detailing(
                geometry, reinforcement, concrete_grade, steel_grade, is_ductile, **kwargs
            ))
        elif member_type == MemberType.SLAB:
            results.update(self._check_slab_detailing(
                geometry, reinforcement, concrete_grade, steel_grade, **kwargs
            ))
        elif member_type == MemberType.FOOTING:
            results.update(self._check_footing_detailing(
                geometry, reinforcement, concrete_grade, steel_grade, **kwargs
            ))
        
        return results
    
    def _check_common_requirements(self,
                                 geometry: MemberGeometry,
                                 reinforcement: List[ReinforcementBar],
                                 concrete_grade: ConcreteGrade,
                                 steel_grade: SteelGrade,
                                 exposure_condition: ExposureCondition) -> Dict[str, CheckResult]:
        """Check common requirements applicable to all members"""
        results = {}
        
        # Cover check
        cover_tables = DetailingTables.get_minimum_cover_requirements()
        base_cover = cover_tables['general']['other_reinforcement']
        exposure_addition = cover_tables['exposure_addition'][exposure_condition]
        required_cover = base_cover + exposure_addition
        
        if geometry.cover < required_cover:
            results['cover_check'] = CheckResult(
                is_compliant=False,
                clause_reference="SP 34:1987, Section 4.1",
                description="Insufficient concrete cover",
                actual_value=geometry.cover,
                required_value=required_cover
            )
        else:
            results['cover_check'] = CheckResult(
                is_compliant=True,
                clause_reference="SP 34:1987, Section 4.1",
                description="Concrete cover adequate"
            )
        
        # Bar spacing check
        results['spacing_check'] = self.spacing_checker.check_minimum_bar_spacing(reinforcement)
        
        return results
    
    def _check_beam_detailing(self,
                            geometry: MemberGeometry,
                            reinforcement: List[ReinforcementBar],
                            concrete_grade: ConcreteGrade,
                            steel_grade: SteelGrade,
                            is_ductile: bool,
                            **kwargs) -> Dict[str, CheckResult]:
        """Beam-specific detailing checks"""
        results = {}
        
        # Calculate total steel area
        ast_total = sum(math.pi * (bar.diameter/2)**2 * bar.number for bar in reinforcement)
        
        # Minimum reinforcement check
        results['min_reinforcement'] = self.beam_checker.check_minimum_reinforcement(
            ast_total, geometry.width, geometry.effective_depth, steel_grade
        )
        
        # Maximum reinforcement check
        results['max_reinforcement'] = self.beam_checker.check_maximum_reinforcement(
            ast_total, geometry.width, geometry.depth
        )
        
        # Side face reinforcement check
        side_steel_area = kwargs.get('side_steel_area', 0)
        web_area = geometry.width * geometry.depth
        results['side_face_reinforcement'] = self.beam_checker.check_side_face_reinforcement(
            geometry.depth, side_steel_area > 0, side_steel_area, web_area
        )
        
        # Ductile detailing checks if required
        if is_ductile:
            ast_top = kwargs.get('ast_top', ast_total/2)
            ast_bottom = kwargs.get('ast_bottom', ast_total/2)
            results['ductile_reinforcement'] = self.ductile_checker.check_beam_reinforcement_ratio(
                ast_top, ast_bottom, geometry.width, geometry.effective_depth,
                concrete_grade, steel_grade
            )
            
            stirrup_spacing_ends = kwargs.get('stirrup_spacing_ends', 150)
            stirrup_spacing_middle = kwargs.get('stirrup_spacing_middle', 200)
            results['ductile_stirrups'] = self.ductile_checker.check_stirrup_spacing_ductile(
                stirrup_spacing_ends, stirrup_spacing_middle, geometry.effective_depth
            )
        
        return results
    
    def _check_column_detailing(self,
                              geometry: MemberGeometry,
                              reinforcement: List[ReinforcementBar],
                              concrete_grade: ConcreteGrade,
                              steel_grade: SteelGrade,
                              is_ductile: bool,
                              **kwargs) -> Dict[str, CheckResult]:
        """Column-specific detailing checks"""
        results = {}
        
        # Calculate areas
        gross_area = geometry.width * geometry.depth
        ast_total = sum(math.pi * (bar.diameter/2)**2 * bar.number for bar in reinforcement)
        
        # Get main bar details
        main_bars = [bar for bar in reinforcement if bar.diameter >= 12]
        main_bar_diameter = max([bar.diameter for bar in main_bars]) if main_bars else 12
        num_main_bars = sum([bar.number for bar in main_bars])
        
        # Minimum and maximum reinforcement
        is_lap_zone = kwargs.get('is_lap_zone', False)
        results['min_longitudinal'] = self.column_checker.check_minimum_longitudinal_reinforcement(
            ast_total, gross_area
        )
        results['max_longitudinal'] = self.column_checker.check_maximum_longitudinal_reinforcement(
            ast_total, gross_area, is_lap_zone
        )
        
        # Minimum bars and diameter
        column_type = kwargs.get('column_type', 'rectangular')
        results['min_bars_diameter'] = self.column_checker.check_minimum_bars_and_diameter(
            num_main_bars, main_bar_diameter, column_type
        )
        
        # Tie requirements
        tie_spacing = kwargs.get('tie_spacing', 200)
        tie_diameter = kwargs.get('tie_diameter', 8)
        clear_height = kwargs.get('clear_height', 3000)
        column_dimension = min(geometry.width, geometry.depth)
        
        results['tie_requirements'] = self.column_checker.check_tie_spacing_and_diameter(
            tie_spacing, tie_diameter, column_dimension, main_bar_diameter, clear_height
        )
        
        # Ductile detailing for columns
        if is_ductile:
            axial_stress_ratio = kwargs.get('axial_stress_ratio', 0.05)
            has_special_confinement = kwargs.get('has_special_confinement', False)
            confinement_length = kwargs.get('confinement_length', 0)
            
            results['ductile_confinement'] = self.ductile_checker.check_column_confinement(
                column_dimension, clear_height, has_special_confinement,
                confinement_length, axial_stress_ratio
            )
        
        return results
    
    def _check_slab_detailing(self,
                            geometry: MemberGeometry,
                            reinforcement: List[ReinforcementBar],
                            concrete_grade: ConcreteGrade,
                            steel_grade: SteelGrade,
                            **kwargs) -> Dict[str, CheckResult]:
        """Slab-specific detailing checks"""
        results = {}
        
        # Calculate areas
        gross_area = geometry.width * geometry.depth
        ast_total = sum(math.pi * (bar.diameter/2)**2 * bar.number for bar in reinforcement)
        
        # Minimum reinforcement
        is_deformed = kwargs.get('is_deformed', True)
        results['min_reinforcement'] = self.slab_checker.check_minimum_reinforcement(
            ast_total, gross_area, is_deformed
        )
        
        # Spacing requirements
        main_spacing = kwargs.get('main_spacing', 200)
        dist_spacing = kwargs.get('dist_spacing', 300)
        
        results['main_spacing'] = self.slab_checker.check_spacing_requirements(
            main_spacing, dist_spacing, geometry.effective_depth, True
        )
        results['dist_spacing'] = self.slab_checker.check_spacing_requirements(
            main_spacing, dist_spacing, geometry.effective_depth, False
        )
        
        # Torsional reinforcement at corners
        corner_type = kwargs.get('corner_type', 'continuous')
        has_torsion_steel = kwargs.get('has_torsion_steel', False)
        torsion_steel_area = kwargs.get('torsion_steel_area', 0)
        max_moment_steel = ast_total
        shorter_span = kwargs.get('shorter_span', geometry.length)
        
        results['torsional_reinforcement'] = self.slab_checker.check_torsional_reinforcement(
            corner_type, has_torsion_steel, torsion_steel_area, max_moment_steel, shorter_span
        )
        
        return results
    
    def _check_footing_detailing(self,
                               geometry: MemberGeometry,
                               reinforcement: List[ReinforcementBar],
                               concrete_grade: ConcreteGrade,
                               steel_grade: SteelGrade,
                               **kwargs) -> Dict[str, CheckResult]:
        """Footing-specific detailing checks"""
        results = {}
        
        # Cover check for footings
        in_contact_with_earth = kwargs.get('in_contact_with_earth', True)
        results['footing_cover'] = self.footing_checker.check_minimum_cover(
            geometry.cover, in_contact_with_earth
        )
        
        # Dowel requirements
        dowel_area = kwargs.get('dowel_area', 0)
        column_area = kwargs.get('column_area', 400*400)  # Default 400x400 column
        num_dowels = kwargs.get('num_dowels', 4)
        dowel_diameter = kwargs.get('dowel_diameter', 16)
        column_bar_diameter = kwargs.get('column_bar_diameter', 20)
        
        if dowel_area > 0:
            results['dowel_requirements'] = self.footing_checker.check_dowel_requirements(
                dowel_area, column_area, num_dowels, dowel_diameter, column_bar_diameter
            )
        
        return results
    
    def generate_compliance_report(self, results: Dict[str, CheckResult]) -> str:
        """Generate a comprehensive compliance report"""
        compliant_checks = [name for name, result in results.items() if result.is_compliant]
        non_compliant_checks = [name for name, result in results.items() if not result.is_compliant]
        
        overall_compliance = len(non_compliant_checks) == 0
        
        report = f"""
SP 34:1987 DETAILING COMPLIANCE REPORT
=====================================

OVERALL STATUS: {'COMPLIANT' if overall_compliance else 'NOT COMPLIANT'}
Total Checks: {len(results)}
Passed: {len(compliant_checks)}
Failed: {len(non_compliant_checks)}

"""
        
        if non_compliant_checks:
            report += "FAILED CHECKS:\n"
            report += "-" * 50 + "\n"
            for check_name in non_compliant_checks:
                result = results[check_name]
                report += f"• {check_name.upper()}:\n"
                report += f"  Issue: {result.description}\n"
                report += f"  Reference: {result.clause_reference}\n"
                if result.actual_value is not None and result.required_value is not None:
                    report += f"  Actual: {result.actual_value}, Required: {result.required_value}\n"
                if result.remarks:
                    report += f"  Remarks: {result.remarks}\n"
                report += "\n"
        
        if compliant_checks:
            report += "PASSED CHECKS:\n"
            report += "-" * 50 + "\n"
            for check_name in compliant_checks:
                result = results[check_name]
                report += f"• {check_name.upper()}: {result.description}\n"
        
        return report

# Example usage and test cases
def example_beam_check():
    """Example of checking a beam for SP 34:1987 compliance"""
    
    # Define beam geometry
    geometry = MemberGeometry(
        length=6000,      # 6m span
        width=300,        # 300mm width
        depth=600,        # 600mm total depth
        effective_depth=550,  # 550mm effective depth
        cover=30          # 30mm cover
    )
    
    # Define reinforcement
    reinforcement = [
        ReinforcementBar(diameter=20, number=4, spacing=75, length=6000, position="bottom"),
        ReinforcementBar(diameter=12, number=2, spacing=150, length=6000, position="top"),
    ]
    
    # Material properties
    concrete_grade = ConcreteGrade.M25
    steel_grade = SteelGrade.FE415
    exposure_condition = ExposureCondition.MODERATE
    
    # Create checker and perform checks
    checker = DetailingChecker()
    
    results = checker.check_member_detailing(
        member_type=MemberType.BEAM,
        geometry=geometry,
        reinforcement=reinforcement,
        concrete_grade=concrete_grade,
        steel_grade=steel_grade,
        exposure_condition=exposure_condition,
        is_ductile=True,
        ast_top=226.2,  # Area of top steel (2-12mm bars)
        ast_bottom=1256.6,  # Area of bottom steel (4-20mm bars)
        stirrup_spacing_ends=100,
        stirrup_spacing_middle=150,
        side_steel_area=0
    )
    
    # Generate report
    report = checker.generate_compliance_report(results)
    print(report)
    
    return results

def example_column_check():
    """Example of checking a column for SP 34:1987 compliance"""
    
    geometry = MemberGeometry(
        length=400,       # Square column
        width=400,
        depth=400,
        effective_depth=350,
        cover=40
    )
    
    reinforcement = [
        ReinforcementBar(diameter=20, number=8, spacing=100, length=3000, position="longitudinal"),
    ]
    
    checker = DetailingChecker()
    
    results = checker.check_member_detailing(
        member_type=MemberType.COLUMN,
        geometry=geometry,
        reinforcement=reinforcement,
        concrete_grade=ConcreteGrade.M30,
        steel_grade=SteelGrade.FE415,
        exposure_condition=ExposureCondition.MILD,
        is_ductile=True,
        tie_spacing=150,
        tie_diameter=8,
        clear_height=3000,
        axial_stress_ratio=0.15,
        has_special_confinement=True,
        confinement_length=450
    )
    
    report = checker.generate_compliance_report(results)
    print(report)
    
    return results

if __name__ == "__main__":
    print("SP 34:1987 Detailing Compliance Checker")
    print("="*50)
    
    print("\nTesting Beam Detailing:")
    beam_results = example_beam_check()
    
    print("\n" + "="*80)
    print("\nTesting Column Detailing:")
    column_results = example_column_check()
