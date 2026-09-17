// Synthetic compatibility sensitivity. No language inputs, inference or API.
// Reuse the already tested matrix format, PRNG and quantile implementation.
#define main previous_numeric_study_main
#include "../decision-and-design-2026-09-16/bootstrap_oc.cpp"
#undef main

struct Design {
    std::string name;
    double english;
    std::array<double,2> original, replica;
    bool imbalance=false, shared_frames=false, missing_arm=false;
};

std::vector<Design> designs() {
    return {
        {"equal_mid",.80,{.80,.80},{.80,.80}},
        {"equal_high",.95,{.95,.95},{.95,.95}},
        {"one_form_separated_5pp",.80,{.80,.80},{.85,.80}},
        {"both_forms_separated_10pp",.80,{.80,.80},{.90,.90}},
        {"opposite_form_shifts_10pp",.80,{.80,.80},{.90,.70}},
        {"equal_imbalanced",.80,{.80,.80},{.80,.80},true},
        {"separated_10pp_imbalanced",.80,{.80,.80},{.90,.90},true},
        {"equal_near_ceiling",.999,{.999,.999},{.999,.999}},
        {"equal_near_floor",.001,{.001,.001},{.001,.001}},
        {"equal_shared_frames",.80,{.80,.80},{.80,.80},false,true},
        {"separated_10pp_shared_frames",.80,{.80,.80},{.90,.90},false,true},
        {"unobservable_arm_sentinel",.80,{.80,.80},{.80,.80},false,false,true},
    };
}

struct Study {
    std::array<Interval,3> bounds{};
    std::array<double,3> point{};
    bool held=false, degenerate=false, generic_resolution_guard=false;
    unsigned accepted=0;
};

Study study(const Matrix& m, const std::array<double,2>& pa, double pe,
            bool shared_frames, RNG& rng, bool fixture=false) {
    Study result;
    std::array<std::vector<double>,2> values;
    for (unsigned f=0; f<2; ++f) {
        std::vector<unsigned> ac(m.n),ec(m.n),an(m.n),en(m.n);
        unsigned tac=0,tec=0,tan=0,ten=0;
        double shared=0; bool use_shared=false;
        for (unsigned i=0; i<m.n; ++i) {
            if (i%4==0) { shared=rng.uniform(); use_shared=shared_frames && rng.uniform()<.7; }
            for (unsigned r=0; r<2; ++r) {
                const bool a=m.arms[(f*m.n+i)*2+r];
                const bool correct=fixture ? ((i+2*r+f)%5!=0)
                    : (use_shared ? shared : rng.uniform()) < (a ? pa[f] : pe);
                if(a) { ++an[i]; ac[i]+=correct; } else { ++en[i]; ec[i]+=correct; }
            }
            tac+=ac[i];tec+=ec[i];tan+=an[i];ten+=en[i];
        }
        if(!tan || !ten) { result.held=true; return result; }
        const double aa=register_round(double(tac)/tan),ee=register_round(double(tec)/ten);
        result.point[f]=register_round(100*(aa-ee));
        result.degenerate |= tac==0 || tac==tan || tec==0 || tec==ten;
        // Current CAD accuracy resolution with the explicitly assumed two-option chance .5.
        result.generic_resolution_guard |= (aa>=.90 && ee>=.90) || (aa<=.55 && ee<=.55);
        values[f].resize(m.draws);
        for(unsigned b=0;b<m.draws;++b) {
            unsigned cac=0,cec=0,can=0,cen=0;
            const uint16_t* w=m.weights.data()+(f*m.draws+b)*m.n;
            for(unsigned i=0;i<m.n;++i) {
                cac+=w[i]*ac[i];cec+=w[i]*ec[i];can+=w[i]*an[i];cen+=w[i]*en[i];
            }
            values[f][b]=(can && cen) ? 100*(double(cac)/can-double(cec)/cen)
                : std::numeric_limits<double>::quiet_NaN();
        }
    }
    std::array<std::vector<double>,3> accepted;
    for(unsigned b=0;b<m.draws;++b) {
        if(!std::isfinite(values[0][b]) || !std::isfinite(values[1][b])) continue;
        accepted[0].push_back(values[0][b]);accepted[1].push_back(values[1][b]);
        accepted[2].push_back(.5*values[0][b]+.5*values[1][b]);
    }
    result.accepted=accepted[0].size();
    if(!result.accepted) { result.held=true;return result; }
    for(unsigned f=0;f<3;++f) result.bounds[f]=quantile(accepted[f]);
    result.point[2]=register_round(.5*result.point[0]+.5*result.point[1]);
    return result;
}

bool intersects(Interval a,Interval b) {
    a=published(a);b=published(b);
    return a.lo<=b.hi && b.lo<=a.hi;
}

int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--plan") {
            std::cout<<"case,english,original_form0,original_form1,replica_form0,replica_form1,imbalance,shared_frames,missing_arm\n";
            for(const auto& d:designs())std::cout<<d.name<<","<<d.english<<","<<d.original[0]<<","<<d.original[1]<<","<<d.replica[0]<<","<<d.replica[1]<<","<<d.imbalance<<","<<d.shared_frames<<","<<d.missing_arm<<"\n";
            return 0;
        }
        if(argc<3)throw std::runtime_error("usage: compatibility MATRIX0 MATRIX1 [TRIALS [CASE]]");
        Matrix baseA(argv[1]),baseB(argv[2]);
        if(baseA.n!=baseB.n)throw std::runtime_error("sizes differ");
        int trials=argc>3?std::stoi(argv[3]):500;
        if(trials<1 || trials>100000)throw std::runtime_error("invalid trials");
        std::string selected=argc>4?argv[4]:"all";
        std::cout<<std::setprecision(12);
        if(selected=="fixture" || selected=="perfect_fixture") {
            RNG r{42};auto x=study(baseA,{selected=="fixture"?.8:1.,selected=="fixture"?.8:1.},selected=="fixture"?.8:1.,false,r,selected=="fixture");
            for(unsigned f=0;f<3;++f)std::cout<<f<<","<<x.point[f]<<","<<x.bounds[f].lo<<","<<x.bounds[f].hi<<","<<x.accepted<<","<<x.degenerate<<","<<x.generic_resolution_guard<<"\n";
            return 0;
        }
        std::cout<<"case,n_per_form,trials,observable_pairs,new_interval_compatible,current_point_strata_compatible,held_pairs,original_degenerate_arm,replica_degenerate_arm,original_generic_resolution_guard,invalid_bootstrap_draws,mean_original_form0_width\n";
        bool matched=false;auto cases=designs();
        for(size_t k=0;k<cases.size();++k) {
            const auto& d=cases[k];if(selected!="all" && selected!=d.name)continue;
            matched=true;Matrix a=baseA,b=baseB;
            if(d.imbalance)for(unsigned f=0;f<2;++f)for(unsigned i=0;i<a.n;++i)for(unsigned r=0;r<2;++r) {
                a.arms[(f*a.n+i)*2+r]=(2*i+r)%8==0;
                b.arms[(f*b.n+i)*2+r]=(2*i+r+3)%8==0;
            }
            if(d.missing_arm)for(unsigned i=0;i<b.n;++i)for(unsigned r=0;r<2;++r)b.arms[(b.n+i)*2+r]=0;
            unsigned observable=0,agree=0,current=0,held=0,degA=0,degB=0,guard=0,validA=0;
            uint64_t invalid=0;double width=0;
            for(int t=0;t<trials;++t) {
                RNG ra{0x917ac03942100000ULL+(uint64_t(a.n)<<24)+(k<<16)+uint64_t(t)*2};
                RNG rb{0x917ac03942100001ULL+(uint64_t(a.n)<<24)+(k<<16)+uint64_t(t)*2};
                auto x=study(a,d.original,d.english,d.shared_frames,ra);
                auto y=study(b,d.replica,d.english,d.shared_frames,rb);
                invalid+=2*a.draws-x.accepted-y.accepted;
                degA+=!x.held && x.degenerate;degB+=!y.held && y.degenerate;
                guard+=!x.held && x.generic_resolution_guard;
                if(!x.held){++validA;width+=x.bounds[0].hi-x.bounds[0].lo;}
                if(x.held || y.held){++held;continue;}
                ++observable;
                bool proposed=true,legacy=intersects(x.bounds[2],y.bounds[2]);
                for(unsigned f=0;f<3;++f)proposed &= intersects(x.bounds[f],y.bounds[f]);
                for(unsigned f=0;f<2;++f)legacy &= std::abs(x.point[f]-y.point[f])<=std::max(.02,.1*std::abs(x.point[f]));
                agree+=proposed;current+=legacy;
            }
            std::cout<<d.name<<","<<a.n<<","<<trials<<","<<observable<<","<<agree<<","<<current<<","<<held<<","<<degA<<","<<degB<<","<<guard<<","<<invalid<<","<<(validA?width/validA:0)<<"\n"<<std::flush;
        }
        if(!matched)throw std::runtime_error("unknown case");
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
