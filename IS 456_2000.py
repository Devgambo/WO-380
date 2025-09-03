"""
IS 456:2000 Compliance Checker for RCC Structures
A comprehensive program for checking compliance with IS 456:2000 code provisions

Key Features:
1) Modular Design: Separate classes for different types of checks (Material, Durability, Flexural, Shear, Deflection, Detailing)

2) Complete Coverage:
--Material properties and grades
--Durability requirements (exposure conditions, cover)
--Limit state design (flexure, shear)
--Serviceability (deflection control)
--Reinforcement detailing

3) Clause References: Each check references specific IS 456:2000 clauses

4) Comprehensive Output:
--Pass/Fail status for each check
--Utilization ratios
--Specific recommendations
--Detailed compliance report

5) Usage Example

# Create a design checker
checker = DesignChecker()

# Define your structure
material = Material(fck=25, fy=415)
dimensions = Dimensions(length=5000, width=300, depth=500, effective_depth=450, cover=25)
loads = Loads(dead_load=15, live_load=10)
reinforcement = Reinforcement(main_steel_area=1256, main_bar_dia=20)

# Check compliance
results = checker.check_compliance(
    member_type=MemberType.BEAM,
    dimensions=dimensions,
    material=material,
    loads=loads,
    exposure=ExposureCondition.MODERATE,
    reinforcement=reinforcement
)

# Generate report
report = checker.generate_compliance_report(results)
print(report)

"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum

# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class MemberType(Enum):
    BEAM = "beam"
    SLAB = "slab"
    COLUMN = "column"
    FOOTING = "footing"
    STAIR = "stair"

class ExposureCondition(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    VERY_SEVERE = "very_severe"
    EXTREME = "extreme"

class ConcreteGrade(Enum):
    M15 = 15
    M20 = 20
    M25 = 25
    M30 = 30
    M35 = 35
    M40 = 40
    M45 = 45
    M50 = 50

class SteelGrade(Enum):
    FE250 = 250
    FE415 = 415
    FE500 = 500

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Material:
    """Material properties as per IS 456:2000"""
    fck: float  # Characteristic compressive strength of concrete
    fy: float   # Characteristic strength of steel
    gamma_c: float = 1.5  # Partial safety factor for concrete
    gamma_s: float = 1.15 # Partial safety factor for steel
    Es: float = 200000    # Modulus of elasticity of steel (N/mm²)
    
    def __post_init__(self):
        # Calculate Ec as per Clause 6.2.3.1
        self.Ec = 5000 * math.sqrt(self.fck)  # N/mm²

@dataclass
class Loads:
    """Load combinations as per IS 456:2000 Clause 36.4.1"""
    dead_load: float = 0
    live_load: float = 0
    wind_load: float = 0
    earthquake_load: float = 0
    
    def get_factored_loads(self) -> Dict[str, float]:
        """Calculate factored loads for limit state design"""
        combinations = {
            'DL+LL': 1.5 * self.dead_load + 1.5 * self.live_load,
            'DL+WL': 1.5 * self.dead_load + 1.5 * self.wind_load,
            'DL+LL+WL': 1.2 * self.dead_load + 1.2 * self.live_load + 1.2 * self.wind_load
        }
        return combinations

@dataclass
class Dimensions:
    """Member dimensions"""
    length: float = 0
    width: float = 0
    depth: float = 0
    effective_depth: float = 0
    cover: float = 0

@dataclass
class Reinforcement:
    """Reinforcement details"""
    main_steel_area: float = 0
    distribution_steel_area: float = 0
    shear_steel_area: float = 0
    main_bar_dia: float = 0
    distribution_bar_dia: float = 0
    stirrup_dia: float = 0
    stirrup_spacing: float = 0

# =============================================================================
# COMPLIANCE CHECKER CLASSES
# =============================================================================

class MaterialCompliance:
    """Check material compliance as per IS 456:2000"""
    
    @staticmethod
    def check_concrete_grade(fck: float) -> Tuple[bool, str]:
        """Check concrete grade compliance - Clause 6.1"""
        valid_grades = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
        
        if fck not in valid_grades:
            return False, f"Clause 6.1: Invalid concrete grade M{fck}. Valid grades: {valid_grades}"
        
        return True, f"Concrete grade M{fck} is valid"
    
    @staticmethod
    def check_steel_grade(fy: float) -> Tuple[bool, str]:
        """Check steel grade compliance"""
        valid_grades = [250, 415, 500]
        
        if fy not in valid_grades:
            return False, f"Invalid steel grade Fe{fy}. Valid grades: {valid_grades}"
        
        return True, f"Steel grade Fe{fy} is valid"
    
    @staticmethod
    def check_minimum_grade_requirements(member_type: MemberType, fck: float, 
                                       exposure: ExposureCondition) -> Tuple[bool, str]:
        """Check minimum grade requirements - Clause 6.1.2, Table 5"""
        min_grades = {
            ExposureCondition.MILD: {'plain': 15, 'reinforced': 20},
            ExposureCondition.MODERATE: {'plain': 15, 'reinforced': 25},
            ExposureCondition.SEVERE: {'plain': 20, 'reinforced': 30},
            ExposureCondition.VERY_SEVERE: {'plain': 20, 'reinforced': 35},
            ExposureCondition.EXTREME: {'plain': 25, 'reinforced': 40}
        }
        
        req_grade = min_grades[exposure]['reinforced']  # Assuming reinforced concrete
        
        if fck < req_grade:
            return False, (f"Clause 6.1.2: Minimum concrete grade for {exposure.value} "
                          f"exposure is M{req_grade}, provided M{fck}")
        
        return True, f"Concrete grade M{fck} satisfies minimum requirement for {exposure.value} exposure"

class DurabilityCompliance:
    """Check durability requirements as per IS 456:2000 Section 8"""
    
    @staticmethod
    def get_minimum_cover(exposure: ExposureCondition) -> float:
        """Get minimum cover as per Clause 26.4.2, Table 16"""
        cover_requirements = {
            ExposureCondition.MILD: 20,
            ExposureCondition.MODERATE: 30,
            ExposureCondition.SEVERE: 45,
            ExposureCondition.VERY_SEVERE: 50,
            ExposureCondition.EXTREME: 75
        }
        return cover_requirements[exposure]
    
    @staticmethod
    def check_cover_requirements(cover: float, exposure: ExposureCondition, 
                               bar_dia: float) -> Tuple[bool, str]:
        """Check cover requirements - Clause 26.4"""
        min_cover = DurabilityCompliance.get_minimum_cover(exposure)
        
        # Cover should not be less than bar diameter
        min_cover = max(min_cover, bar_dia)
        
        if cover < min_cover:
            return False, (f"Clause 26.4.2: Minimum cover required is {min_cover}mm "
                          f"for {exposure.value} exposure, provided {cover}mm")
        
        return True, f"Cover {cover}mm satisfies requirement for {exposure.value} exposure"
    
    @staticmethod
    def check_cement_content_and_wcr(exposure: ExposureCondition, fck: float) -> Tuple[bool, str]:
        """Check cement content and water-cement ratio - Clause 8.2.4.1, Table 5"""
        requirements = {
            ExposureCondition.MILD: {'min_cement': 300, 'max_wcr': 0.55},
            ExposureCondition.MODERATE: {'min_cement': 300, 'max_wcr': 0.50},
            ExposureCondition.SEVERE: {'min_cement': 320, 'max_wcr': 0.45},
            ExposureCondition.VERY_SEVERE: {'min_cement': 340, 'max_wcr': 0.45},
            ExposureCondition.EXTREME: {'min_cement': 360, 'max_wcr': 0.40}
        }
        
        req = requirements[exposure]
        return True, (f"Minimum cement content: {req['min_cement']} kg/m³, "
                     f"Maximum W/C ratio: {req['max_wcr']}")

class FlexuralCompliance:
    """Check flexural compliance as per IS 456:2000 Section 5"""
    
    @staticmethod
    def check_minimum_steel(member_type: MemberType, Ast: float, b: float, d: float, 
                           fy: float) -> Tuple[bool, str]:
        """Check minimum steel requirements - Clause 26.5.1.1"""
        
        if member_type == MemberType.BEAM:
            min_steel = (0.85 * b * d) / fy  # Clause 26.5.1.1(a)
        elif member_type == MemberType.SLAB:
            if fy <= 250:
                min_steel = 0.0015 * b * d  # Clause 26.5.2.1
            else:
                min_steel = 0.0012 * b * d
        else:
            min_steel = 0.0012 * b * d  # Conservative approach
            
        if Ast < min_steel:
            return False, (f"Clause 26.5: Minimum steel required is {min_steel:.0f}mm², "
                          f"provided {Ast:.0f}mm²")
        
        return True, f"Minimum steel requirement satisfied"
    
    @staticmethod
    def check_maximum_steel(Ast: float, b: float, D: float) -> Tuple[bool, str]:
        """Check maximum steel requirements - Clause 26.5.1.1(b)"""
        max_steel = 0.04 * b * D
        
        if Ast > max_steel:
            return False, (f"Clause 26.5.1.1: Maximum steel allowed is {max_steel:.0f}mm², "
                          f"provided {Ast:.0f}mm²")
        
        return True, f"Maximum steel requirement satisfied"
    
    @staticmethod
    def calculate_moment_capacity(b: float, d: float, Ast: float, fck: float, 
                                fy: float) -> Tuple[float, Dict[str, float]]:
        """Calculate moment capacity using LSM - Clause 38"""
        
        # Limiting depth of neutral axis
        xu_max_by_d = 0.48 if fy == 415 else (0.46 if fy == 500 else 0.53)
        xu_max = xu_max_by_d * d
        
        # Depth of neutral axis
        xu = (0.87 * fy * Ast) / (0.36 * fck * b)
        
        if xu <= xu_max:
            # Under-reinforced section
            Mu = 0.87 * fy * Ast * (d - 0.42 * xu)
        else:
            # Over-reinforced section - use limiting moment
            Mu = 0.36 * fck * b * d**2 * xu_max_by_d * (1 - 0.42 * xu_max_by_d)
        
        analysis = {
            'xu': xu,
            'xu_max': xu_max,
            'section_type': 'under-reinforced' if xu <= xu_max else 'over-reinforced'
        }
        
        return Mu / 1e6, analysis  # Convert to kNm

class ShearCompliance:
    """Check shear compliance as per IS 456:2000 Clause 40"""
    
    @staticmethod
    def calculate_design_shear_strength(b: float, d: float, Ast: float, fck: float) -> float:
        """Calculate design shear strength of concrete - Table 19"""
        
        # Steel percentage
        pt = (100 * Ast) / (b * d)
        pt = min(pt, 3.0)  # Upper limit for table
        
        # Simplified calculation based on Table 19
        if fck == 15:
            if pt <= 0.15:
                tc = 0.28
            elif pt <= 0.25:
                tc = 0.35
            elif pt <= 0.50:
                tc = 0.46
            elif pt <= 0.75:
                tc = 0.54
            elif pt <= 1.00:
                tc = 0.60
            elif pt <= 1.25:
                tc = 0.64
            elif pt <= 1.50:
                tc = 0.68
            elif pt <= 1.75:
                tc = 0.71
            elif pt <= 2.00:
                tc = 0.71
            else:
                tc = 0.71
        elif fck == 20:
            if pt <= 0.15:
                tc = 0.28
            elif pt <= 0.25:
                tc = 0.36
            elif pt <= 0.50:
                tc = 0.48
            elif pt <= 0.75:
                tc = 0.56
            elif pt <= 1.00:
                tc = 0.62
            elif pt <= 1.25:
                tc = 0.67
            elif pt <= 1.50:
                tc = 0.72
            elif pt <= 1.75:
                tc = 0.75
            elif pt <= 2.00:
                tc = 0.79
            else:
                tc = 0.82
        elif fck >= 25:
            # Interpolation for higher grades
            base_values = [0.29, 0.36, 0.49, 0.57, 0.64, 0.70, 0.74, 0.78, 0.82, 0.85]
            grade_factor = min(1.0 + (fck - 25) / 100, 1.2)  # Conservative approach
            pt_index = min(int(pt * 2), len(base_values) - 1)
            tc = base_values[pt_index] * grade_factor
        else:
            tc = 0.28  # Conservative for lower grades
        
        return tc
    
    @staticmethod
    def check_shear_capacity(Vu: float, b: float, d: float, Ast: float, 
                           fck: float) -> Tuple[bool, str, Dict[str, float]]:
        """Check shear capacity - Clause 40"""
        
        # Nominal shear stress
        tv = Vu * 1000 / (b * d)  # Convert kN to N
        
        # Design shear strength of concrete
        tc = ShearCompliance.calculate_design_shear_strength(b, d, Ast, fck)
        
        # Maximum shear stress allowed (Table 20)
        tc_max_values = {15: 2.5, 20: 2.8, 25: 3.1, 30: 3.5, 35: 3.7, 40: 4.0}
        tc_max = tc_max_values.get(fck, 4.0)
        
        analysis = {
            'tv': tv,
            'tc': tc,
            'tc_max': tc_max,
            'shear_reinforcement_required': tv > tc
        }
        
        if tv > tc_max:
            return False, (f"Clause 40.2.3: Nominal shear stress {tv:.2f} N/mm² exceeds "
                          f"maximum allowed {tc_max} N/mm²"), analysis
        elif tv > tc:
            return True, (f"Shear reinforcement required. tv={tv:.2f} > tc={tc:.2f} N/mm²"), analysis
        else:
            return True, f"No shear reinforcement required. tv={tv:.2f} ≤ tc={tc:.2f} N/mm²", analysis

class DeflectionCompliance:
    """Check deflection requirements as per IS 456:2000 Clause 23.2"""
    
    @staticmethod
    def get_basic_span_to_depth_ratios() -> Dict[str, float]:
        """Basic span to effective depth ratios - Clause 23.2.1(a)"""
        return {
            'cantilever': 7,
            'simply_supported': 20,
            'continuous': 26
        }
    
    @staticmethod
    def check_span_to_depth_ratio(span: float, effective_depth: float, 
                                support_condition: str, Ast_provided: float,
                                Ast_required: float, fck: float, fy: float) -> Tuple[bool, str]:
        """Check span to depth ratio - Clause 23.2"""
        
        basic_ratios = DeflectionCompliance.get_basic_span_to_depth_ratios()
        basic_ratio = basic_ratios.get(support_condition, 20)
        
        # Modification factor for tension reinforcement (Fig. 4)
        fs = 0.58 * fy * (Ast_required / Ast_provided)  # Stress in steel at service loads
        
        # Simplified modification factor calculation
        if fs <= 150:
            mf_tension = 2.0
        elif fs <= 200:
            mf_tension = 1.5
        elif fs <= 250:
            mf_tension = 1.2
        elif fs <= 300:
            mf_tension = 1.0
        else:
            mf_tension = 0.8
        
        # For spans over 10m
        span_factor = min(10.0 / span, 1.0) if span > 10 else 1.0
        
        allowable_ratio = basic_ratio * mf_tension * span_factor
        actual_ratio = span / effective_depth
        
        if actual_ratio > allowable_ratio:
            return False, (f"Clause 23.2: Span to depth ratio {actual_ratio:.1f} exceeds "
                          f"allowable {allowable_ratio:.1f}")
        
        return True, f"Span to depth ratio {actual_ratio:.1f} is within allowable {allowable_ratio:.1f}"

class ReinforcementDetailing:
    """Check reinforcement detailing as per IS 456:2000 Section 26"""
    
    @staticmethod
    def check_spacing_requirements(spacing: float, member_type: MemberType, 
                                 bar_dia: float, effective_depth: float, aggregate_size: float = 20) -> Tuple[bool, str]:
        """Check spacing requirements - Clause 26.3"""
        
        # Minimum spacing requirements
        min_spacing = max(bar_dia, 5 + aggregate_size)  # Clause 26.3.2(a)
        
        if member_type == MemberType.SLAB:
            max_spacing = min(3 * effective_depth, 300)
        else:
            max_spacing = 300  # Conservative
        
        if spacing < min_spacing:
            return False, (f"Clause 26.3.2: Minimum spacing required is {min_spacing}mm, "
                          f"provided {spacing}mm")
        
        if spacing > max_spacing:
            return False, (f"Clause 26.3.3: Maximum spacing allowed is {max_spacing}mm, "
                          f"provided {spacing}mm")
        
        return True, f"Bar spacing {spacing}mm is within limits"
    
    @staticmethod
    def calculate_development_length(bar_dia: float, fck: float, fy: float,
                                   bond_condition: str = 'tension') -> float:
        """Calculate development length - Clause 26.2.1"""
        
        # Design bond stress (Table in Clause 26.2.1.1)
        if fck == 20:
            tbd = 1.2
        elif fck == 25:
            tbd = 1.4
        elif fck == 30:
            tbd = 1.5
        elif fck == 35:
            tbd = 1.7
        elif fck >= 40:
            tbd = 1.9
        else:
            tbd = 1.2  # Conservative
        
        # For deformed bars, increase by 60%
        tbd *= 1.6
        
        # For bars in compression, increase by 25%
        if bond_condition == 'compression':
            tbd *= 1.25
        
        # Development length
        Ld = (0.87 * fy * bar_dia) / (4 * tbd)
        
        return Ld

# =============================================================================
# MAIN DESIGN CHECKER CLASS
# =============================================================================

class DesignChecker:
    """Main class for IS 456:2000 compliance checking"""
    
    def __init__(self):
        self.material_checker = MaterialCompliance()
        self.durability_checker = DurabilityCompliance()
        self.flexure_checker = FlexuralCompliance()
        self.shear_checker = ShearCompliance()
        self.deflection_checker = DeflectionCompliance()
        self.detailing_checker = ReinforcementDetailing()
    
    def check_compliance(self, member_type: MemberType, dimensions: Dimensions,
                        material: Material, loads: Loads, exposure: ExposureCondition,
                        reinforcement: Reinforcement, support_condition: str = 'simply_supported') -> Dict:
        """
        Comprehensive compliance check for RCC member
        
        Args:
            member_type: Type of structural member
            dimensions: Member dimensions
            material: Material properties
            loads: Applied loads
            exposure: Exposure condition
            reinforcement: Reinforcement details
            support_condition: Support condition for deflection check
            
        Returns:
            Dictionary containing compliance results
        """
        
        results = {
            'overall_compliance': True,
            'failed_checks': [],
            'passed_checks': [],
            'utilization_ratios': {},
            'recommendations': []
        }
        
        # Material compliance checks
        try:
            # Check concrete grade
            is_valid, msg = self.material_checker.check_concrete_grade(material.fck)
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
            # Check steel grade
            is_valid, msg = self.material_checker.check_steel_grade(material.fy)
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
            # Check minimum grade requirements
            is_valid, msg = self.material_checker.check_minimum_grade_requirements(
                member_type, material.fck, exposure)
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
        except Exception as e:
            results['failed_checks'].append(f"Material check error: {str(e)}")
            results['overall_compliance'] = False
        
        # Durability compliance checks
        try:
            # Check cover requirements
            is_valid, msg = self.durability_checker.check_cover_requirements(
                dimensions.cover, exposure, reinforcement.main_bar_dia)
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
            # Check cement content and W/C ratio
            is_valid, msg = self.durability_checker.check_cement_content_and_wcr(
                exposure, material.fck)
            results['passed_checks'].append(msg)
            
        except Exception as e:
            results['failed_checks'].append(f"Durability check error: {str(e)}")
            results['overall_compliance'] = False
        
        # Flexural compliance checks
        try:
            # Check minimum steel
            is_valid, msg = self.flexure_checker.check_minimum_steel(
                member_type, reinforcement.main_steel_area, 
                dimensions.width, dimensions.effective_depth, material.fy)
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
            # Check maximum steel
            is_valid, msg = self.flexure_checker.check_maximum_steel(
                reinforcement.main_steel_area, dimensions.width, dimensions.depth)
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
            # Calculate moment capacity and utilization
            factored_loads = loads.get_factored_loads()
            max_factored_load = max(factored_loads.values())
            
            # Approximate moment calculation (for simply supported beam)
            if member_type == MemberType.BEAM:
                Mu_applied = max_factored_load * dimensions.length**2 / 8  # kNm
            else:
                Mu_applied = max_factored_load * dimensions.length**2 / 12  # kNm (conservative)
            
            Mu_capacity, flexural_analysis = self.flexure_checker.calculate_moment_capacity(
                dimensions.width, dimensions.effective_depth, 
                reinforcement.main_steel_area, material.fck, material.fy)
            
            utilization_flexure = Mu_applied / Mu_capacity if Mu_capacity > 0 else float('inf')
            results['utilization_ratios']['flexure'] = utilization_flexure
            
            if utilization_flexure > 1.0:
                results['failed_checks'].append(
                    f"Flexural capacity insufficient: Utilization = {utilization_flexure:.2f}")
                results['overall_compliance'] = False
            else:
                results['passed_checks'].append(
                    f"Flexural capacity adequate: Utilization = {utilization_flexure:.2f}")
            
        except Exception as e:
            results['failed_checks'].append(f"Flexural check error: {str(e)}")
            results['overall_compliance'] = False
        
        # Shear compliance checks
        try:
            # Approximate shear calculation
            Vu_applied = max_factored_load * dimensions.length / 2  # kN
            
            is_valid, msg, shear_analysis = self.shear_checker.check_shear_capacity(
                Vu_applied, dimensions.width, dimensions.effective_depth,
                reinforcement.main_steel_area, material.fck)
            
            if is_valid:
                results['passed_checks'].append(msg)
                if shear_analysis['shear_reinforcement_required']:
                    results['recommendations'].append(
                        "Provide shear reinforcement as per IS 456:2000 Clause 40.4")
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
            results['utilization_ratios']['shear'] = shear_analysis['tv'] / shear_analysis['tc_max']
            
        except Exception as e:
            results['failed_checks'].append(f"Shear check error: {str(e)}")
            results['overall_compliance'] = False
        
        # Deflection compliance checks
        try:
            is_valid, msg = self.deflection_checker.check_span_to_depth_ratio(
                dimensions.length, dimensions.effective_depth, support_condition,
                reinforcement.main_steel_area, reinforcement.main_steel_area * 0.8,  # Assumed required
                material.fck, material.fy)
            
            if is_valid:
                results['passed_checks'].append(msg)
            else:
                results['failed_checks'].append(msg)
                results['overall_compliance'] = False
            
        except Exception as e:
            results['failed_checks'].append(f"Deflection check error: {str(e)}")
            results['overall_compliance'] = False
        
        # Detailing checks
        try:
            # Check main steel spacing
            if reinforcement.main_steel_area > 0:
                # Approximate spacing calculation
                bar_area = math.pi * (reinforcement.main_bar_dia/2)**2
                num_bars = reinforcement.main_steel_area / bar_area
                spacing = (dimensions.width - 2 * dimensions.cover) / (num_bars - 1) if num_bars > 1 else dimensions.width
                
                is_valid, msg = self.detailing_checker.check_spacing_requirements(
                    spacing, member_type, reinforcement.main_bar_dia, dimensions.effective_depth)
                
                if is_valid:
                    results['passed_checks'].append(msg)
                else:
                    results['failed_checks'].append(msg)
                    results['overall_compliance'] = False
            
            # Calculate development length
            Ld = self.detailing_checker.calculate_development_length(
                reinforcement.main_bar_dia, material.fck, material.fy)
            
            results['recommendations'].append(
                f"Required development length: {Ld:.0f}mm (Clause 26.2.1)")
            
        except Exception as e:
            results['failed_checks'].append(f"Detailing check error: {str(e)}")
            results['overall_compliance'] = False
        
        return results
    
    def generate_compliance_report(self, results: Dict) -> str:
        """Generate a formatted compliance report"""
        
        report = "="*80 + "\n"
        report += "IS 456:2000 COMPLIANCE REPORT\n"
        report += "="*80 + "\n\n"
        
        # Overall compliance status
        status = "COMPLIANT" if results['overall_compliance'] else "NOT COMPLIANT"
        report += f"OVERALL STATUS: {status}\n\n"
        
        # Failed checks
        if results['failed_checks']:
            report += "FAILED CHECKS:\n"
            report += "-"*50 + "\n"
            for i, check in enumerate(results['failed_checks'], 1):
                report += f"{i}. {check}\n"
            report += "\n"
        
        # Passed checks
        if results['passed_checks']:
            report += "PASSED CHECKS:\n"
            report += "-"*50 + "\n"
            for i, check in enumerate(results['passed_checks'], 1):
                report += f"{i}. {check}\n"
            report += "\n"
        
        # Utilization ratios
        if results['utilization_ratios']:
            report += "UTILIZATION RATIOS:\n"
            report += "-"*50 + "\n"
            for component, ratio in results['utilization_ratios'].items():
                report += f"{component.upper()}: {ratio:.3f}\n"
            report += "\n"
        
        # Recommendations
        if results['recommendations']:
            report += "RECOMMENDATIONS:\n"
            report += "-"*50 + "\n"
            for i, rec in enumerate(results['recommendations'], 1):
                report += f"{i}. {rec}\n"
            report += "\n"
        
        report += "="*80
        
        return report

# =============================================================================
# EXAMPLE USAGE AND TEST CASES
# =============================================================================

def example_beam_check():
    """Example: Check a simply supported beam"""
    
    # Define materials
    material = Material(fck=25, fy=415)  # M25 concrete, Fe415 steel
    
    # Define dimensions
    dimensions = Dimensions(
        length=5000,      # 5m span
        width=300,        # 300mm width
        depth=500,        # 500mm depth
        effective_depth=450,  # 450mm effective depth
        cover=25          # 25mm cover
    )
    
    # Define loads
    loads = Loads(
        dead_load=15,     # 15 kN/m
        live_load=10      # 10 kN/m
    )
    
    # Define reinforcement
    reinforcement = Reinforcement(
        main_steel_area=1256,    # 4-20mm bars = 1256 mm²
        main_bar_dia=20,
        stirrup_dia=8,
        stirrup_spacing=150
    )
    
    # Create checker and run compliance check
    checker = DesignChecker()
    results = checker.check_compliance(
        member_type=MemberType.BEAM,
        dimensions=dimensions,
        material=material,
        loads=loads,
        exposure=ExposureCondition.MODERATE,
        reinforcement=reinforcement,
        support_condition='simply_supported'
    )
    
    # Generate and print report
    report = checker.generate_compliance_report(results)
    print(report)
    
    return results

def example_slab_check():
    """Example: Check a two-way slab"""
    
    # Define materials
    material = Material(fck=20, fy=415)
    
    # Define dimensions
    dimensions = Dimensions(
        length=4000,      # 4m span
        width=4000,       # 4m span (square slab)
        depth=150,        # 150mm thick
        effective_depth=120,  # 120mm effective depth
        cover=20          # 20mm cover
    )
    
    # Define loads
    loads = Loads(
        dead_load=5,      # 5 kN/m²
        live_load=4       # 4 kN/m²
    )
    
    # Define reinforcement
    reinforcement = Reinforcement(
        main_steel_area=628,     # 10mm @ 125mm c/c both ways
        main_bar_dia=10,
        distribution_steel_area=628
    )
    
    # Create checker and run compliance check
    checker = DesignChecker()
    results = checker.check_compliance(
        member_type=MemberType.SLAB,
        dimensions=dimensions,
        material=material,
        loads=loads,
        exposure=ExposureCondition.MILD,
        reinforcement=reinforcement,
        support_condition='continuous'
    )
    
    # Generate and print report
    report = checker.generate_compliance_report(results)
    print(report)
    
    return results

# Main execution
if __name__ == "__main__":
    print("IS 456:2000 Compliance Checker")
    print("="*50)
    print("\nExample 1: Simply Supported Beam Check")
    print("-"*50)
    beam_results = example_beam_check()
    
    print("\n\nExample 2: Two-Way Slab Check")
    print("-"*50)
    slab_results = example_slab_check()
    
    # Additional utility functions
    print("\n\nUtility Information:")
    print("-"*50)
    print("Available concrete grades:", [grade.value for grade in ConcreteGrade])
    print("Available steel grades:", [grade.value for grade in SteelGrade])
    print("Available exposure conditions:", [exp.value for exp in ExposureCondition])
    
    # Cover requirements table
    print("\nMinimum Cover Requirements (mm):")
    for exposure in ExposureCondition:
        cover = DurabilityCompliance.get_minimum_cover(exposure)
        print(f"  {exposure.value.title()}: {cover}mm")
