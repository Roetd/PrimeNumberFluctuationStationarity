#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算加权均方误差泛函 I(T, σ)

该脚本用于计算素数波动平稳性猜想中的加权均方误差泛函
I(T, σ) = ∫₀^∞ (Δ(x))² / x^(1+σ) e^(-(x/T)²) dx
其中 Δ(x) = ψ(x) - x，ψ(x) 为第二切比雪夫函数

作者：罗辑
日期：2026-02-10
"""

import numpy as np
from scipy.integrate import quad
from scipy.special import gamma
import matplotlib.pyplot as plt

class ChebyshevFunction:
    """
    第二切比雪夫函数 ψ(x) 的计算
    """
    def __init__(self):
        # 前1000个非平凡零点的虚部（假设黎曼猜想成立，实部均为1/2）
        # 这里使用近似值，实际应用中应从数据库加载
        self.gamma_values = self._get_approximate_gamma_values()
    
    def _get_approximate_gamma_values(self):
        """
        获取近似的零点虚部值
        实际应用中应从精确的零点数据库加载
        """
        # 生成前100个零点的近似值（实际应用中应使用更精确的数据）
        gamma_values = []
        # 前几个已知零点的虚部（更精确的值）
        known_gammas = [
            14.134725141734693,
            21.022039638771554,
            25.010857580145686,
            30.424876125859516,
            32.93506158773919,
            37.58617815882567,
            40.91871901214749,
            43.32707328091499,
            48.00515088116616,
            49.773832477672314
        ]
        gamma_values.extend(known_gammas)
        
        # 近似生成更多零点
        for i in range(10, 100):
            # 更精确的零点间距近似公式
            n = i + 1
            approx_gamma = 2 * np.pi * n / np.log(n / (2 * np.pi))
            gamma_values.append(approx_gamma)
        
        return gamma_values
    
    def psi(self, x):
        """
        计算 ψ(x) = Σ_{p^k ≤ x} log p
        对于大x，使用近似公式：ψ(x) ≈ x - Σ_{|γ| ≤ T} x^ρ / ρ
        """
        if x < 2:
            return 0.0
        
        # 对于小x，使用直接计算
        if x < 1000:
            return self._direct_psi(x)
        
        # 对于大x，使用零点近似
        T = min(x, 1000)  # 限制T的大小，避免计算过多零点
        sum_term = 0.0
        
        for gamma in self.gamma_values:
            if gamma > T:
                break
            
            # 假设黎曼猜想成立，ρ = 1/2 + iγ
            beta = 0.5
            rho = beta + 1j * gamma
            
            # 计算 x^ρ / ρ
            try:
                # 使用复数指数计算，提高精度
                term = np.exp(rho * np.log(x)) / rho
                sum_term += term
            except:
                # 处理数值溢出
                break
        
        # 加上共轭项
        sum_term += np.conj(sum_term)
        
        # 加上常数项 -ζ'(0)/ζ(0) ≈ 0.0461914179
        constant_term = 0.0461914179
        
        return x - sum_term.real - constant_term
    
    def _direct_psi(self, x):
        """
        直接计算 ψ(x) 对于小x
        """
        # 这里使用简化的实现，实际应用中应使用更高效的算法
        result = 0.0
        primes = self._sieve_of_eratosthenes(int(x))
        
        for p in primes:
            k = 1
            while p**k <= x:
                result += np.log(p)
                k += 1
        
        return result
    
    def _sieve_of_eratosthenes(self, n):
        """
        埃拉托斯特尼筛法生成素数
        """
        if n < 2:
            return []
        
        sieve = [True] * (n + 1)
        sieve[0] = sieve[1] = False
        
        for i in range(2, int(np.sqrt(n)) + 1):
            if sieve[i]:
                sieve[i*i : n+1 : i] = [False] * len(sieve[i*i : n+1 : i])
        
        return [i for i, is_prime in enumerate(sieve) if is_prime]

class WeightedMeanSquareError:
    """
    计算加权均方误差泛函 I(T, σ)
    """
    def __init__(self):
        self.chebyshev = ChebyshevFunction()
    
    def delta(self, x):
        """
        计算 Δ(x) = ψ(x) - x
        """
        return self.chebyshev.psi(x) - x
    
    def integrand(self, x, T, sigma):
        """
        被积函数：(Δ(x))² / x^(1+σ) e^(-(x/T)²)
        """
        if x <= 0:
            return 0.0
        
        delta_x = self.delta(x)
        weight = np.exp(-(x / T)**2)
        denominator = x ** (1 + sigma)
        
        return (delta_x ** 2) * weight / denominator
    
    def calculate_I(self, T, sigma, integration_limit=None):
        """
        计算 I(T, σ) = ∫₀^∞ (Δ(x))² / x^(1+σ) e^(-(x/T)²) dx
        
        参数:
            T: 尺度参数
            sigma: 权重参数
            integration_limit: 积分上限（截断），默认 None 表示自动计算
        
        返回:
            I(T, σ) 的数值积分结果
        """
        # 自动计算积分上限，基于权重函数 e^(-(x/T)^2)
        if integration_limit is None:
            integration_limit = 5 * T  # 权重函数在 5T 处已经非常小
        
        # 分段积分，提高精度
        def split_integral(a, b, n=5):
            """分段积分"""
            points = np.linspace(a, b, n+1)
            result = 0.0
            for i in range(n):
                segment_result, _ = quad(self.integrand, points[i], points[i+1], 
                                       args=(T, sigma), limit=200, epsabs=1e-10, epsrel=1e-10)
                result += segment_result
            return result
        
        # 分段积分
        result = split_integral(0, integration_limit)
        
        return result

class AsymptoticAnalysis:
    """
    渐近分析工具
    """
    def __init__(self):
        self.wmse = WeightedMeanSquareError()
    
    def fit_C(self, sigma, T_values):
        """
        拟合 C(σ)，假设 I(T, σ) ~ C(σ) T^(1-2σ)
        
        参数:
            sigma: 权重参数
            T_values: T 的取值列表
        
        返回:
            C(σ) 的拟合值
        """
        I_values = []
        for T in T_values:
            I = self.wmse.calculate_I(T, sigma)
            I_values.append(I)
            print(f"Calculated I({T}, {sigma}) = {I}")
        
        # 取对数
        log_T = np.log(T_values)
        log_I = np.log(I_values)
        
        # 理论斜率
        theoretical_slope = 1 - 2 * sigma
        
        # 拟合截距
        intercept = np.mean(log_I - theoretical_slope * log_T)
        C = np.exp(intercept)
        
        return C
    
    def analyze_oscillation(self, T_values, sigma):
        """
        分析振荡项
        """
        C = self.fit_C(sigma, T_values)
        oscillations = []
        
        for T in T_values:
            I = self.wmse.calculate_I(T, sigma)
            expected = C * (T ** (1 - 2 * sigma))
            osc = abs(I - expected) / expected
            oscillations.append(osc)
            print(f"Oscillation at T={T}, σ={sigma}: {osc}")
        
        return oscillations

def main():
    """
    主函数
    """
    print("素数波动平稳性猜想 - 数值验证")
    print("=" * 50)
    
    # 初始化分析工具
    analyzer = AsymptoticAnalysis()
    
    # 测试参数
    T_values = [100, 316, 1000, 3162, 10000, 31622, 100000]  # 增加更大的T值
    sigma_values = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]  # 增加边界σ值
    
    print("\n1. 计算 I(T, σ) 值:")
    print("-" * 50)
    
    # 计算并打印结果
    results = {}
    for sigma in sigma_values:
        results[sigma] = []
        print(f"\nσ = {sigma}:")
        for T in T_values:
            I = analyzer.wmse.calculate_I(T, sigma)
            results[sigma].append(I)
            print(f"  T = {T:6d}: I = {I:.6e}")
    
    print("\n2. 拟合 C(σ):")
    print("-" * 50)
    
    C_values = {}
    for sigma in sigma_values:
        C = analyzer.fit_C(sigma, T_values)
        C_values[sigma] = C
        print(f"σ = {sigma}: C(σ) = {C:.6e}")
    
    print("\n3. 分析振荡项:")
    print("-" * 50)
    
    for sigma in sigma_values:
        oscillations = analyzer.analyze_oscillation(T_values, sigma)
        print(f"σ = {sigma}: Max oscillation = {max(oscillations):.6f}")
    
    # 绘制结果
    print("\n4. 生成图表:")
    print("-" * 50)
    
    # 绘制 I(T, σ) 随 T 的变化
    plt.figure(figsize=(12, 8))
    for sigma in sigma_values:
        plt.loglog(T_values, results[sigma], 'o-', label=f'σ={sigma}')
    plt.xlabel('T')
    plt.ylabel('I(T, σ)')
    plt.title('Weighted Mean Square Error Function')
    plt.legend()
    plt.grid(True)
    plt.savefig('I_vs_T.png')
    print("Saved I_vs_T.png")
    
    # 绘制 C(σ) 曲线
    plt.figure(figsize=(12, 8))
    plt.plot(sigma_values, [C_values[sigma] for sigma in sigma_values], 'o-')
    plt.xlabel('σ')
    plt.ylabel('C(σ)')
    plt.title('C(σ) vs σ')
    plt.grid(True)
    plt.savefig('C_vs_sigma.png')
    print("Saved C_vs_sigma.png")

if __name__ == "__main__":
    main()
