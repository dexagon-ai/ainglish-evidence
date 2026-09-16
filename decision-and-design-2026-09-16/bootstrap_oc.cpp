// Synthetic design sensitivity only. No language data, inference or network.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

struct RNG {
    uint64_t state;
    uint64_t next() { // SplitMix64, fully specified rather than library distributions.
        uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
        z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        return z ^ (z >> 31);
    }
    double uniform() { return (next() >> 11) * 0x1.0p-53; }
};

struct Matrix {
    uint32_t n, draws, forms, readers;
    std::vector<uint8_t> arms;
    std::vector<uint16_t> weights;
    explicit Matrix(const std::string& path) {
        const uint16_t endian = 1;
        if (*reinterpret_cast<const uint8_t*>(&endian) != 1)
            throw std::runtime_error("binary build inputs require little-endian host");
        std::ifstream input(path, std::ios::binary);
        char magic[8]; input.read(magic, 8);
        if (!input || std::string(magic, 8) != std::string("AINGOC1\0", 8))
            throw std::runtime_error("bad or missing matrix header");
        input.read(reinterpret_cast<char*>(&n), 4);
        input.read(reinterpret_cast<char*>(&draws), 4);
        input.read(reinterpret_cast<char*>(&forms), 4);
        input.read(reinterpret_cast<char*>(&readers), 4);
        if (n < 4 || n > 1250 || draws != 2000 || forms != 2 || readers != 2)
            throw std::runtime_error("unexpected matrix dimensions");
        arms.resize(4*n); weights.resize(2*draws*n);
        input.read(reinterpret_cast<char*>(arms.data()), arms.size());
        input.read(reinterpret_cast<char*>(weights.data()), weights.size()*2);
        if (!input || input.peek() != std::char_traits<char>::eof())
            throw std::runtime_error("truncated or trailing matrix bytes");
        for (auto arm : arms) if (arm > 1) throw std::runtime_error("bad arm");
        for (unsigned f=0; f<2; ++f) for (unsigned b=0; b<draws; ++b) {
            unsigned sum=0;
            for (unsigned i=0; i<n; ++i) sum += weights[(f*draws+b)*n+i];
            if (sum != n) throw std::runtime_error("draw is not n sampled worlds");
        }
    }
};

struct Scenario {
    std::string name;
    std::array<double,2> pa, pe;
    double shared_probability=0, missing=0;
    unsigned cluster_worlds=1;
    bool form_masking=false;
};

std::vector<Scenario> scenarios() {
    return {
        {"equality_independent", {.95,.95}, {.95,.95}},
        {"equality_shared_world", {.95,.95}, {.95,.95}, 1},
        {"tolerated_two_point_loss", {.94,.94}, {.96,.96}},
        {"five_point_boundary", {.90,.90}, {.95,.95}},
        {"six_point_violation", {.89,.89}, {.95,.95}},
        {"boundary_shared_world", {.90,.90}, {.95,.95}, .7},
        {"violation_shared_four_world_frame", {.89,.89}, {.95,.95}, .7, 0, 4},
        {"equality_shared_four_world_frame", {.95,.95}, {.95,.95}, .7, 0, 4},
        {"equality_near_ceiling", {.999,.999}, {.999,.999}},
        {"opposite_reader_effects", {.99,.91}, {.91,.99}},
        {"one_harmed_form_hidden_by_pool", {.97,.97}, {.95,.95}, 0, 0, 1, true},
        {"one_percent_absent_at_random", {.95,.95}, {.95,.95}, 0, .01},
    };
}

struct Interval { double lo, hi; };
double register_round(double x) { return std::round(x*10000.0)/10000.0; }
Interval published(Interval x) { return {register_round(x.lo),register_round(x.hi)}; }
Interval quantile(std::vector<double> values) {
    if (values.empty()) throw std::runtime_error("no accepted draw");
    const size_t li=25*values.size()/1000, hi=975*values.size()/1000;
    std::nth_element(values.begin(), values.begin()+li, values.end());
    const double lower=values[li];
    std::nth_element(values.begin(), values.begin()+hi, values.end());
    return {lower, values[hi]};
}

struct Result {
    std::array<Interval,3> interval; // forms 0, 1 and their equal-weight aggregate.
    std::array<double,3> point, expected;
    bool degenerate=false, supports=false, opposes=false, negative=false;
};

Result evaluate(const Matrix& m, const Scenario& s, RNG& rng, bool fixed_fixture=false) {
    std::array<std::vector<double>,2> values;
    std::array<bool,2> degenerate{};
    Result result;
    for (unsigned f=0; f<2; ++f) {
        std::vector<uint16_t> ac(m.n), ec(m.n), an(m.n), en(m.n);
        unsigned total_ac=0,total_ec=0,total_an=0,total_en=0;
        std::array<unsigned,2> observed_a{}, observed_e{};
        double shared=0; bool use_shared=false;
        for (unsigned i=0; i<m.n; ++i) {
            if (i % s.cluster_worlds == 0) {
                shared=rng.uniform(); use_shared=rng.uniform()<s.shared_probability;
            }
            for (unsigned r=0; r<2; ++r) {
                const bool a=m.arms[(f*m.n+i)*2+r];
                const double p=a ? (s.form_masking && f==1 ? .87 : s.pa[r]) : s.pe[r];
                const bool absent=!fixed_fixture && rng.uniform()<s.missing;
                const bool correct=fixed_fixture ? ((i+2*r+f)%5 != 0)
                                                : (use_shared ? shared : rng.uniform()) < p;
                if (absent) continue;
                if (a) { ++an[i]; ac[i]+=correct; ++observed_a[r]; }
                else { ++en[i]; ec[i]+=correct; ++observed_e[r]; }
            }
            total_ac+=ac[i]; total_ec+=ec[i]; total_an+=an[i]; total_en+=en[i];
        }
        if (!total_an || !total_en) throw std::runtime_error("unobservable main arm");
        result.point[f]=100.0*(double(total_ac)/total_an-double(total_ec)/total_en);
        const auto pa=s.form_masking && f==1 ? std::array<double,2>{.87,.87} : s.pa;
        const auto expected_mean=[](const std::array<double,2>& p,
                                    const std::array<unsigned,2>& counts, unsigned total) {
            // Avoid accumulation error moving a known zero estimand outside [0,0].
            return p[0]==p[1] ? p[0] : (counts[0]*p[0]+counts[1]*p[1])/total;
        };
        result.expected[f]=100.0*(expected_mean(pa,observed_a,total_an)
                                -expected_mean(s.pe,observed_e,total_en));
        degenerate[f]=(total_ac==0 || total_ac==total_an || total_ec==0 || total_ec==total_en);
        result.degenerate |= degenerate[f];
        values[f].resize(m.draws);
        for (unsigned b=0; b<m.draws; ++b) {
            const uint16_t* w=m.weights.data()+(f*m.draws+b)*m.n;
            unsigned cac=0,cec=0,can=0,cen=0;
            for (unsigned i=0; i<m.n; ++i) {
                cac+=unsigned(w[i])*ac[i]; cec+=unsigned(w[i])*ec[i];
                can+=unsigned(w[i])*an[i]; cen+=unsigned(w[i])*en[i];
            }
            values[f][b]=(can && cen) ? 100.0*(double(cac)/can-double(cec)/cen)
                                    : std::numeric_limits<double>::quiet_NaN();
        }
    }
    std::array<std::vector<double>,3> accepted;
    for (unsigned b=0; b<m.draws; ++b) {
        if (!std::isfinite(values[0][b]) || !std::isfinite(values[1][b])) continue;
        accepted[0].push_back(values[0][b]); accepted[1].push_back(values[1][b]);
        accepted[2].push_back(.5*values[0][b]+.5*values[1][b]);
    }
    for (unsigned f=0; f<3; ++f) result.interval[f]=quantile(accepted[f]);
    result.point[2]=.5*(result.point[0]+result.point[1]);
    result.expected[2]=.5*(result.expected[0]+result.expected[1]);
    result.supports=!result.degenerate;
    for (unsigned f=0; f<3; ++f) {
        const auto reported=published(result.interval[f]);
        result.supports &= reported.lo >= -5;
        const bool inadmissible=f<2 ? degenerate[f] : result.degenerate;
        result.opposes |= !inadmissible && reported.hi < -5;
    }
    result.negative=!result.degenerate && published(result.interval[2]).hi < 0;
    return result;
}

bool overlap(const Result& a, const Result& b) {
    for (unsigned f=0; f<3; ++f) {
        const auto ai=published(a.interval[f]), bi=published(b.interval[f]);
        if (ai.lo>bi.hi || bi.lo>ai.hi) return false;
    }
    return true;
}

int main(int argc, char** argv) {
    try {
        if (argc<3) throw std::runtime_error("usage: bootstrap_oc MATRIX0 MATRIX1 [TRIALS [SCENARIO]]");
        Matrix a(argv[1]), b(argv[2]);
        if (a.n!=b.n) throw std::runtime_error("study sizes differ");
        const int trials=argc>3 ? std::stoi(argv[3]) : 1000;
        if (trials<1) throw std::runtime_error("trials must be positive");
        const std::string selected=argc>4 ? argv[4] : "all";
        std::cout<<std::setprecision(12);
        if (selected=="fixture") {
            RNG rng{42}; const auto r=evaluate(a,scenarios()[0],rng,true);
            for (unsigned f=0; f<3; ++f)
                std::cout<<f<<","<<r.point[f]<<","<<r.interval[f].lo<<","<<r.interval[f].hi<<"\n";
            return 0;
        }
        if (selected=="perfect_guard_fixture") {
            RNG rng{42}; const Scenario s{"perfect",{1,1},{1,1}};
            const auto r=evaluate(a,s,rng);
            for (unsigned f=0; f<3; ++f)
                std::cout<<f<<","<<r.expected[f]<<","<<r.interval[f].lo<<","<<r.interval[f].hi
                         <<","<<r.degenerate<<","<<r.supports<<"\n";
            return 0;
        }
        std::cout<<"scenario,n_worlds_per_form,trials,support_original,support_replica,support_both,"
                   "support_both_and_overlap,support_overlap_and_original_negative,opposes_original,"
                   "degenerate_original,cover_form0,cover_form1,cover_pooled,mean_width_form0,"
                   "mean_expected_delta_form0,mean_expected_delta_form1\n";
        auto ss=scenarios(); bool matched=false;
        for (size_t k=0; k<ss.size(); ++k) {
            const auto& s=ss[k]; if (selected!="all" && selected!=s.name) continue;
            matched=true; unsigned sa=0,sb=0,both=0,agree=0,negative=0,opp=0,deg=0;
            std::array<unsigned,3> cover{}; double width=0,e0=0,e1=0;
            // Predeclared independent streams for each simulated study pair and scenario.
            for (int trial=0; trial<trials; ++trial) {
                RNG ra{0x63d4f729a8510000ULL + (uint64_t(a.n)<<24) + (k<<16) + uint64_t(trial)*2};
                RNG rb{0x63d4f729a8510001ULL + (uint64_t(a.n)<<24) + (k<<16) + uint64_t(trial)*2};
                const auto ar=evaluate(a,s,ra), br=evaluate(b,s,rb);
                sa+=ar.supports; sb+=br.supports; both+=ar.supports && br.supports;
                const bool passed=ar.supports && br.supports && overlap(ar,br);
                agree+=passed; negative+=passed && ar.negative;
                opp+=ar.opposes; deg+=ar.degenerate;
                for (unsigned f=0; f<3; ++f) {
                    const auto ci=published(ar.interval[f]);
                    cover[f]+=ci.lo-1e-10<=ar.expected[f] && ar.expected[f]<=ci.hi+1e-10;
                }
                width+=ar.interval[0].hi-ar.interval[0].lo;
                e0+=ar.expected[0]; e1+=ar.expected[1];
            }
            std::cout<<s.name<<","<<a.n<<","<<trials<<","<<sa<<","<<sb<<","<<both<<","
                     <<agree<<","<<negative<<","<<opp<<","<<deg<<","<<cover[0]<<","<<cover[1]
                     <<","<<cover[2]<<","<<width/trials<<","<<e0/trials<<","<<e1/trials<<"\n"<<std::flush;
        }
        if (!matched) throw std::runtime_error("unknown scenario");
    } catch (const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
