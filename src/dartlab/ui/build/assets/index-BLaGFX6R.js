var Yd=Object.defineProperty;var ji=e=>{throw TypeError(e)};var Jd=(e,t,a)=>t in e?Yd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:a}):e[t]=a;var ga=(e,t,a)=>Jd(e,typeof t!="symbol"?t+"":t,a),Do=(e,t,a)=>t.has(e)||ji("Cannot "+a);var O=(e,t,a)=>(Do(e,t,"read from private field"),a?a.call(e):t.get(e)),xt=(e,t,a)=>t.has(e)?ji("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,a),st=(e,t,a,n)=>(Do(e,t,"write to private field"),n?n.call(e,a):t.set(e,a),a),wr=(e,t,a)=>(Do(e,t,"access private method"),a);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const l of document.querySelectorAll('link[rel="modulepreload"]'))n(l);new MutationObserver(l=>{for(const o of l)if(o.type==="childList")for(const s of o.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&n(s)}).observe(document,{childList:!0,subtree:!0});function a(l){const o={};return l.integrity&&(o.integrity=l.integrity),l.referrerPolicy&&(o.referrerPolicy=l.referrerPolicy),l.crossOrigin==="use-credentials"?o.credentials="include":l.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function n(l){if(l.ep)return;l.ep=!0;const o=a(l);fetch(l.href,o)}})();const Uo=!1;var mi=Array.isArray,Xd=Array.prototype.indexOf,ol=Array.prototype.includes,xo=Array.from,Qd=Object.defineProperty,cn=Object.getOwnPropertyDescriptor,ys=Object.getOwnPropertyDescriptors,Zd=Object.prototype,ec=Array.prototype,bi=Object.getPrototypeOf,Di=Object.isExtensible;function _l(e){return typeof e=="function"}const tc=()=>{};function rc(e){return e()}function Wo(e){for(var t=0;t<e.length;t++)e[t]()}function ws(){var e,t,a=new Promise((n,l)=>{e=n,t=l});return{promise:a,resolve:e,reject:t}}function lo(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const a=[];for(const n of e)if(a.push(n),a.length===t)break;return a}const Dr=2,ul=4,Dn=8,mo=1<<24,bn=16,Sa=32,Vn=64,Ko=128,da=512,Pr=1024,Rr=2048,Ca=4096,Hr=8192,Pa=16384,vl=32768,Ka=65536,qi=1<<17,ac=1<<18,fl=1<<19,ks=1<<20,Ia=1<<25,qn=65536,Yo=1<<21,gi=1<<22,un=1<<23,Ra=Symbol("$state"),Cs=Symbol("legacy props"),nc=Symbol(""),Cn=new class extends Error{constructor(){super(...arguments);ga(this,"name","StaleReactionError");ga(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var gs;const Ss=!!((gs=globalThis.document)!=null&&gs.contentType)&&globalThis.document.contentType.includes("xml");function lc(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function oc(e,t,a){throw new Error("https://svelte.dev/e/each_key_duplicate")}function ic(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function sc(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function dc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function cc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function uc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function vc(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function fc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function pc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function xc(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const mc=1,bc=2,Es=4,gc=8,hc=16,_c=1,yc=2,Ms=4,wc=8,kc=16,Cc=1,Sc=2,zr=Symbol(),zs="http://www.w3.org/1999/xhtml",Ts="http://www.w3.org/2000/svg",Ec="http://www.w3.org/1998/Math/MathML",Mc="@attach";function zc(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Tc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function As(e){return e===this.v}function Ac(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Ns(e){return!Ac(e,this.v)}let Il=!1,Nc=!1;function Oc(){Il=!0}let Ar=null;function il(e){Ar=e}function fa(e,t=!1,a){Ar={p:Ar,i:!1,c:null,e:null,s:e,x:null,l:Il&&!t?{s:null,u:null,$:[]}:null}}function pa(e){var t=Ar,a=t.e;if(a!==null){t.e=null;for(var n of a)Xs(n)}return t.i=!0,Ar=t.p,{}}function Ll(){return!Il||Ar!==null&&Ar.l===null}let Sn=[];function Os(){var e=Sn;Sn=[],Wo(e)}function ja(e){if(Sn.length===0&&!El){var t=Sn;queueMicrotask(()=>{t===Sn&&Os()})}Sn.push(e)}function Ic(){for(;Sn.length>0;)Os()}function Is(e){var t=pt;if(t===null)return ft.f|=un,e;if((t.f&vl)===0&&(t.f&ul)===0)throw e;dn(e,t)}function dn(e,t){for(;t!==null;){if((t.f&Ko)!==0){if((t.f&vl)===0)throw e;try{t.b.error(e);return}catch(a){e=a}}t=t.parent}throw e}const Lc=-7169;function gr(e,t){e.f=e.f&Lc|t}function hi(e){(e.f&da)!==0||e.deps===null?gr(e,Pr):gr(e,Ca)}function Ls(e){if(e!==null)for(const t of e)(t.f&Dr)===0||(t.f&qn)===0||(t.f^=qn,Ls(t.deps))}function Ps(e,t,a){(e.f&Rr)!==0?t.add(e):(e.f&Ca)!==0&&a.add(e),Ls(e.deps),gr(e,Pr)}const Jl=new Set;let Ke=null,oo=null,Lr=null,Kr=[],bo=null,El=!1,sl=null,Pc=1;var ln,Qn,Tn,Zn,el,tl,on,Ta,rl,Xr,Jo,Xo,Qo,Zo;const Ai=class Ai{constructor(){xt(this,Xr);ga(this,"id",Pc++);ga(this,"current",new Map);ga(this,"previous",new Map);xt(this,ln,new Set);xt(this,Qn,new Set);xt(this,Tn,0);xt(this,Zn,0);xt(this,el,null);xt(this,tl,new Set);xt(this,on,new Set);xt(this,Ta,new Map);ga(this,"is_fork",!1);xt(this,rl,!1)}skip_effect(t){O(this,Ta).has(t)||O(this,Ta).set(t,{d:[],m:[]})}unskip_effect(t){var a=O(this,Ta).get(t);if(a){O(this,Ta).delete(t);for(var n of a.d)gr(n,Rr),La(n);for(n of a.m)gr(n,Ca),La(n)}}process(t){var l;Kr=[],this.apply();var a=sl=[],n=[];for(const o of t)wr(this,Xr,Xo).call(this,o,a,n);if(sl=null,wr(this,Xr,Jo).call(this)){wr(this,Xr,Qo).call(this,n),wr(this,Xr,Qo).call(this,a);for(const[o,s]of O(this,Ta))qs(o,s)}else{oo=this,Ke=null;for(const o of O(this,ln))o(this);O(this,ln).clear(),O(this,Tn)===0&&wr(this,Xr,Zo).call(this),$i(n),$i(a),O(this,tl).clear(),O(this,on).clear(),oo=null,(l=O(this,el))==null||l.resolve()}Lr=null}capture(t,a){a!==zr&&!this.previous.has(t)&&this.previous.set(t,a),(t.f&un)===0&&(this.current.set(t,t.v),Lr==null||Lr.set(t,t.v))}activate(){Ke=this,this.apply()}deactivate(){Ke===this&&(Ke=null,Lr=null)}flush(){var t;if(Kr.length>0)Ke=this,Rs();else if(O(this,Tn)===0&&!this.is_fork){for(const a of O(this,ln))a(this);O(this,ln).clear(),wr(this,Xr,Zo).call(this),(t=O(this,el))==null||t.resolve()}this.deactivate()}discard(){for(const t of O(this,Qn))t(this);O(this,Qn).clear()}increment(t){st(this,Tn,O(this,Tn)+1),t&&st(this,Zn,O(this,Zn)+1)}decrement(t){st(this,Tn,O(this,Tn)-1),t&&st(this,Zn,O(this,Zn)-1),!O(this,rl)&&(st(this,rl,!0),ja(()=>{st(this,rl,!1),wr(this,Xr,Jo).call(this)?Kr.length>0&&this.flush():this.revive()}))}revive(){for(const t of O(this,tl))O(this,on).delete(t),gr(t,Rr),La(t);for(const t of O(this,on))gr(t,Ca),La(t);this.flush()}oncommit(t){O(this,ln).add(t)}ondiscard(t){O(this,Qn).add(t)}settled(){return(O(this,el)??st(this,el,ws())).promise}static ensure(){if(Ke===null){const t=Ke=new Ai;Jl.add(Ke),El||ja(()=>{Ke===t&&t.flush()})}return Ke}apply(){}};ln=new WeakMap,Qn=new WeakMap,Tn=new WeakMap,Zn=new WeakMap,el=new WeakMap,tl=new WeakMap,on=new WeakMap,Ta=new WeakMap,rl=new WeakMap,Xr=new WeakSet,Jo=function(){return this.is_fork||O(this,Zn)>0},Xo=function(t,a,n){t.f^=Pr;for(var l=t.first;l!==null;){var o=l.f,s=(o&(Sa|Vn))!==0,d=s&&(o&Pr)!==0,v=(o&Hr)!==0,x=d||O(this,Ta).has(l);if(!x&&l.fn!==null){s?v||(l.f^=Pr):(o&ul)!==0?a.push(l):(o&(Dn|mo))!==0&&v?n.push(l):jl(l)&&(cl(l),(o&bn)!==0&&(O(this,on).add(l),v&&gr(l,Rr)));var g=l.first;if(g!==null){l=g;continue}}for(;l!==null;){var k=l.next;if(k!==null){l=k;break}l=l.parent}}},Qo=function(t){for(var a=0;a<t.length;a+=1)Ps(t[a],O(this,tl),O(this,on))},Zo=function(){var o;if(Jl.size>1){this.previous.clear();var t=Ke,a=Lr,n=!0;for(const s of Jl){if(s===this){n=!1;continue}const d=[];for(const[x,g]of this.current){if(s.current.has(x))if(n&&g!==s.current.get(x))s.current.set(x,g);else continue;d.push(x)}if(d.length===0)continue;const v=[...s.current.keys()].filter(x=>!this.current.has(x));if(v.length>0){var l=Kr;Kr=[];const x=new Set,g=new Map;for(const k of d)js(k,v,x,g);if(Kr.length>0){Ke=s,s.apply();for(const k of Kr)wr(o=s,Xr,Xo).call(o,k,[],[]);s.deactivate()}Kr=l}}Ke=t,Lr=a}O(this,Ta).clear(),Jl.delete(this)};let vn=Ai;function Rc(e){var t=El;El=!0;try{for(var a;;){if(Ic(),Kr.length===0&&(Ke==null||Ke.flush(),Kr.length===0))return bo=null,a;Rs()}}finally{El=t}}function Rs(){var e=null;try{for(var t=0;Kr.length>0;){var a=vn.ensure();if(t++>1e3){var n,l;jc()}a.process(Kr),fn.clear()}}finally{Kr=[],bo=null,sl=null}}function jc(){try{cc()}catch(e){dn(e,bo)}}let ha=null;function $i(e){var t=e.length;if(t!==0){for(var a=0;a<t;){var n=e[a++];if((n.f&(Pa|Hr))===0&&jl(n)&&(ha=new Set,cl(n),n.deps===null&&n.first===null&&n.nodes===null&&n.teardown===null&&n.ac===null&&td(n),(ha==null?void 0:ha.size)>0)){fn.clear();for(const l of ha){if((l.f&(Pa|Hr))!==0)continue;const o=[l];let s=l.parent;for(;s!==null;)ha.has(s)&&(ha.delete(s),o.push(s)),s=s.parent;for(let d=o.length-1;d>=0;d--){const v=o[d];(v.f&(Pa|Hr))===0&&cl(v)}}ha.clear()}}ha=null}}function js(e,t,a,n){if(!a.has(e)&&(a.add(e),e.reactions!==null))for(const l of e.reactions){const o=l.f;(o&Dr)!==0?js(l,t,a,n):(o&(gi|bn))!==0&&(o&Rr)===0&&Ds(l,t,n)&&(gr(l,Rr),La(l))}}function Ds(e,t,a){const n=a.get(e);if(n!==void 0)return n;if(e.deps!==null)for(const l of e.deps){if(ol.call(t,l))return!0;if((l.f&Dr)!==0&&Ds(l,t,a))return a.set(l,!0),!0}return a.set(e,!1),!1}function La(e){var t=bo=e,a=t.b;if(a!=null&&a.is_pending&&(e.f&(ul|Dn|mo))!==0&&(e.f&vl)===0){a.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var n=t.f;if(sl!==null&&t===pt&&(e.f&Dn)===0)return;if((n&(Vn|Sa))!==0){if((n&Pr)===0)return;t.f^=Pr}}Kr.push(t)}function qs(e,t){if(!((e.f&Sa)!==0&&(e.f&Pr)!==0)){(e.f&Rr)!==0?t.d.push(e):(e.f&Ca)!==0&&t.m.push(e),gr(e,Pr);for(var a=e.first;a!==null;)qs(a,t),a=a.next}}function Dc(e){let t=0,a=xn(0),n;return()=>{ki()&&(r(a),Ci(()=>(t===0&&(n=$n(()=>e(()=>zl(a)))),t+=1,()=>{ja(()=>{t-=1,t===0&&(n==null||n(),n=void 0,zl(a))})})))}}var qc=Ka|fl;function $c(e,t,a,n){new Fc(e,t,a,n)}var ia,xi,Aa,An,Wr,Na,ra,_a,Ha,Nn,sn,al,nl,ll,Ua,fo,Sr,Bc,Vc,Gc,ei,to,ro,ti;class Fc{constructor(t,a,n,l){xt(this,Sr);ga(this,"parent");ga(this,"is_pending",!1);ga(this,"transform_error");xt(this,ia);xt(this,xi,null);xt(this,Aa);xt(this,An);xt(this,Wr);xt(this,Na,null);xt(this,ra,null);xt(this,_a,null);xt(this,Ha,null);xt(this,Nn,0);xt(this,sn,0);xt(this,al,!1);xt(this,nl,new Set);xt(this,ll,new Set);xt(this,Ua,null);xt(this,fo,Dc(()=>(st(this,Ua,xn(O(this,Nn))),()=>{st(this,Ua,null)})));var o;st(this,ia,t),st(this,Aa,a),st(this,An,s=>{var d=pt;d.b=this,d.f|=Ko,n(s)}),this.parent=pt.b,this.transform_error=l??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),st(this,Wr,pl(()=>{wr(this,Sr,ei).call(this)},qc))}defer_effect(t){Ps(t,O(this,nl),O(this,ll))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!O(this,Aa).pending}update_pending_count(t){wr(this,Sr,ti).call(this,t),st(this,Nn,O(this,Nn)+t),!(!O(this,Ua)||O(this,al))&&(st(this,al,!0),ja(()=>{st(this,al,!1),O(this,Ua)&&dl(O(this,Ua),O(this,Nn))}))}get_effect_pending(){return O(this,fo).call(this),r(O(this,Ua))}error(t){var a=O(this,Aa).onerror;let n=O(this,Aa).failed;if(!a&&!n)throw t;O(this,Na)&&(jr(O(this,Na)),st(this,Na,null)),O(this,ra)&&(jr(O(this,ra)),st(this,ra,null)),O(this,_a)&&(jr(O(this,_a)),st(this,_a,null));var l=!1,o=!1;const s=()=>{if(l){Tc();return}l=!0,o&&xc(),O(this,_a)!==null&&In(O(this,_a),()=>{st(this,_a,null)}),wr(this,Sr,ro).call(this,()=>{vn.ensure(),wr(this,Sr,ei).call(this)})},d=v=>{try{o=!0,a==null||a(v,s),o=!1}catch(x){dn(x,O(this,Wr)&&O(this,Wr).parent)}n&&st(this,_a,wr(this,Sr,ro).call(this,()=>{vn.ensure();try{return Jr(()=>{var x=pt;x.b=this,x.f|=Ko,n(O(this,ia),()=>v,()=>s)})}catch(x){return dn(x,O(this,Wr).parent),null}}))};ja(()=>{var v;try{v=this.transform_error(t)}catch(x){dn(x,O(this,Wr)&&O(this,Wr).parent);return}v!==null&&typeof v=="object"&&typeof v.then=="function"?v.then(d,x=>dn(x,O(this,Wr)&&O(this,Wr).parent)):d(v)})}}ia=new WeakMap,xi=new WeakMap,Aa=new WeakMap,An=new WeakMap,Wr=new WeakMap,Na=new WeakMap,ra=new WeakMap,_a=new WeakMap,Ha=new WeakMap,Nn=new WeakMap,sn=new WeakMap,al=new WeakMap,nl=new WeakMap,ll=new WeakMap,Ua=new WeakMap,fo=new WeakMap,Sr=new WeakSet,Bc=function(){try{st(this,Na,Jr(()=>O(this,An).call(this,O(this,ia))))}catch(t){this.error(t)}},Vc=function(t){const a=O(this,Aa).failed;a&&st(this,_a,Jr(()=>{a(O(this,ia),()=>t,()=>()=>{})}))},Gc=function(){const t=O(this,Aa).pending;t&&(this.is_pending=!0,st(this,ra,Jr(()=>t(O(this,ia)))),ja(()=>{var a=st(this,Ha,document.createDocumentFragment()),n=Da();a.append(n),st(this,Na,wr(this,Sr,ro).call(this,()=>(vn.ensure(),Jr(()=>O(this,An).call(this,n))))),O(this,sn)===0&&(O(this,ia).before(a),st(this,Ha,null),In(O(this,ra),()=>{st(this,ra,null)}),wr(this,Sr,to).call(this))}))},ei=function(){try{if(this.is_pending=this.has_pending_snippet(),st(this,sn,0),st(this,Nn,0),st(this,Na,Jr(()=>{O(this,An).call(this,O(this,ia))})),O(this,sn)>0){var t=st(this,Ha,document.createDocumentFragment());Mi(O(this,Na),t);const a=O(this,Aa).pending;st(this,ra,Jr(()=>a(O(this,ia))))}else wr(this,Sr,to).call(this)}catch(a){this.error(a)}},to=function(){this.is_pending=!1;for(const t of O(this,nl))gr(t,Rr),La(t);for(const t of O(this,ll))gr(t,Ca),La(t);O(this,nl).clear(),O(this,ll).clear()},ro=function(t){var a=pt,n=ft,l=Ar;va(O(this,Wr)),ua(O(this,Wr)),il(O(this,Wr).ctx);try{return t()}catch(o){return Is(o),null}finally{va(a),ua(n),il(l)}},ti=function(t){var a;if(!this.has_pending_snippet()){this.parent&&wr(a=this.parent,Sr,ti).call(a,t);return}st(this,sn,O(this,sn)+t),O(this,sn)===0&&(wr(this,Sr,to).call(this),O(this,ra)&&In(O(this,ra),()=>{st(this,ra,null)}),O(this,Ha)&&(O(this,ia).before(O(this,Ha)),st(this,Ha,null)))};function $s(e,t,a,n){const l=Ll()?Pl:_i;var o=e.filter(k=>!k.settled);if(a.length===0&&o.length===0){n(t.map(l));return}var s=pt,d=Hc(),v=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(k=>k.promise)):null;function x(k){d();try{n(k)}catch(C){(s.f&Pa)===0&&dn(C,s)}ri()}if(a.length===0){v.then(()=>x(t.map(l)));return}function g(){d(),Promise.all(a.map(k=>Wc(k))).then(k=>x([...t.map(l),...k])).catch(k=>dn(k,s))}v?v.then(g):g()}function Hc(){var e=pt,t=ft,a=Ar,n=Ke;return function(o=!0){va(e),ua(t),il(a),o&&(n==null||n.activate())}}function ri(e=!0){va(null),ua(null),il(null),e&&(Ke==null||Ke.deactivate())}function Uc(){var e=pt.b,t=Ke,a=e.is_rendered();return e.update_pending_count(1),t.increment(a),()=>{e.update_pending_count(-1),t.decrement(a)}}function Pl(e){var t=Dr|Rr,a=ft!==null&&(ft.f&Dr)!==0?ft:null;return pt!==null&&(pt.f|=fl),{ctx:Ar,deps:null,effects:null,equals:As,f:t,fn:e,reactions:null,rv:0,v:zr,wv:0,parent:a??pt,ac:null}}function Wc(e,t,a){pt===null&&lc();var l=void 0,o=xn(zr),s=!ft,d=new Map;return iu(()=>{var C;var v=ws();l=v.promise;try{Promise.resolve(e()).then(v.resolve,v.reject).finally(ri)}catch(R){v.reject(R),ri()}var x=Ke;if(s){var g=Uc();(C=d.get(x))==null||C.reject(Cn),d.delete(x),d.set(x,v)}const k=(R,T=void 0)=>{if(x.activate(),T)T!==Cn&&(o.f|=un,dl(o,T));else{(o.f&un)!==0&&(o.f^=un),dl(o,R);for(const[I,y]of d){if(d.delete(I),I===x)break;y.reject(Cn)}}g&&g()};v.promise.then(k,R=>k(null,R||"unknown"))}),ho(()=>{for(const v of d.values())v.reject(Cn)}),new Promise(v=>{function x(g){function k(){g===l?v(o):x(l)}g.then(k,k)}x(l)})}function se(e){const t=Pl(e);return nd(t),t}function _i(e){const t=Pl(e);return t.equals=Ns,t}function Kc(e){var t=e.effects;if(t!==null){e.effects=null;for(var a=0;a<t.length;a+=1)jr(t[a])}}function Yc(e){for(var t=e.parent;t!==null;){if((t.f&Dr)===0)return(t.f&Pa)===0?t:null;t=t.parent}return null}function yi(e){var t,a=pt;va(Yc(e));try{e.f&=~qn,Kc(e),t=sd(e)}finally{va(a)}return t}function Fs(e){var t=yi(e);if(!e.equals(t)&&(e.wv=od(),(!(Ke!=null&&Ke.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){gr(e,Pr);return}mn||(Lr!==null?(ki()||Ke!=null&&Ke.is_fork)&&Lr.set(e,t):hi(e))}function Jc(e){var t,a;if(e.effects!==null)for(const n of e.effects)(n.teardown||n.ac)&&((t=n.teardown)==null||t.call(n),(a=n.ac)==null||a.abort(Cn),n.teardown=tc,n.ac=null,Al(n,0),Si(n))}function Bs(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&cl(t)}let ai=new Set;const fn=new Map;let Vs=!1;function xn(e,t){var a={f:0,v:e,reactions:null,equals:As,rv:0,wv:0};return a}function D(e,t){const a=xn(e);return nd(a),a}function Xc(e,t=!1,a=!0){var l;const n=xn(e);return t||(n.equals=Ns),Il&&a&&Ar!==null&&Ar.l!==null&&((l=Ar.l).s??(l.s=[])).push(n),n}function c(e,t,a=!1){ft!==null&&(!wa||(ft.f&qi)!==0)&&Ll()&&(ft.f&(Dr|bn|gi|qi))!==0&&(ca===null||!ol.call(ca,e))&&pc();let n=a?yt(t):t;return dl(e,n)}function dl(e,t){if(!e.equals(t)){var a=e.v;mn?fn.set(e,t):fn.set(e,a),e.v=t;var n=vn.ensure();if(n.capture(e,a),(e.f&Dr)!==0){const l=e;(e.f&Rr)!==0&&yi(l),hi(l)}e.wv=od(),Gs(e,Rr),Ll()&&pt!==null&&(pt.f&Pr)!==0&&(pt.f&(Sa|Vn))===0&&(oa===null?du([e]):oa.push(e)),!n.is_fork&&ai.size>0&&!Vs&&Qc()}return t}function Qc(){Vs=!1;for(const e of ai)(e.f&Pr)!==0&&gr(e,Ca),jl(e)&&cl(e);ai.clear()}function Ml(e,t=1){var a=r(e),n=t===1?a++:a--;return c(e,a),n}function zl(e){c(e,e.v+1)}function Gs(e,t){var a=e.reactions;if(a!==null)for(var n=Ll(),l=a.length,o=0;o<l;o++){var s=a[o],d=s.f;if(!(!n&&s===pt)){var v=(d&Rr)===0;if(v&&gr(s,t),(d&Dr)!==0){var x=s;Lr==null||Lr.delete(x),(d&qn)===0&&(d&da&&(s.f|=qn),Gs(x,Ca))}else v&&((d&bn)!==0&&ha!==null&&ha.add(s),La(s))}}}function yt(e){if(typeof e!="object"||e===null||Ra in e)return e;const t=bi(e);if(t!==Zd&&t!==ec)return e;var a=new Map,n=mi(e),l=D(0),o=Ln,s=d=>{if(Ln===o)return d();var v=ft,x=Ln;ua(null),Gi(o);var g=d();return ua(v),Gi(x),g};return n&&a.set("length",D(e.length)),new Proxy(e,{defineProperty(d,v,x){(!("value"in x)||x.configurable===!1||x.enumerable===!1||x.writable===!1)&&vc();var g=a.get(v);return g===void 0?s(()=>{var k=D(x.value);return a.set(v,k),k}):c(g,x.value,!0),!0},deleteProperty(d,v){var x=a.get(v);if(x===void 0){if(v in d){const g=s(()=>D(zr));a.set(v,g),zl(l)}}else c(x,zr),zl(l);return!0},get(d,v,x){var R;if(v===Ra)return e;var g=a.get(v),k=v in d;if(g===void 0&&(!k||(R=cn(d,v))!=null&&R.writable)&&(g=s(()=>{var T=yt(k?d[v]:zr),I=D(T);return I}),a.set(v,g)),g!==void 0){var C=r(g);return C===zr?void 0:C}return Reflect.get(d,v,x)},getOwnPropertyDescriptor(d,v){var x=Reflect.getOwnPropertyDescriptor(d,v);if(x&&"value"in x){var g=a.get(v);g&&(x.value=r(g))}else if(x===void 0){var k=a.get(v),C=k==null?void 0:k.v;if(k!==void 0&&C!==zr)return{enumerable:!0,configurable:!0,value:C,writable:!0}}return x},has(d,v){var C;if(v===Ra)return!0;var x=a.get(v),g=x!==void 0&&x.v!==zr||Reflect.has(d,v);if(x!==void 0||pt!==null&&(!g||(C=cn(d,v))!=null&&C.writable)){x===void 0&&(x=s(()=>{var R=g?yt(d[v]):zr,T=D(R);return T}),a.set(v,x));var k=r(x);if(k===zr)return!1}return g},set(d,v,x,g){var H;var k=a.get(v),C=v in d;if(n&&v==="length")for(var R=x;R<k.v;R+=1){var T=a.get(R+"");T!==void 0?c(T,zr):R in d&&(T=s(()=>D(zr)),a.set(R+"",T))}if(k===void 0)(!C||(H=cn(d,v))!=null&&H.writable)&&(k=s(()=>D(void 0)),c(k,yt(x)),a.set(v,k));else{C=k.v!==zr;var I=s(()=>yt(x));c(k,I)}var y=Reflect.getOwnPropertyDescriptor(d,v);if(y!=null&&y.set&&y.set.call(g,x),!C){if(n&&typeof v=="string"){var M=a.get("length"),F=Number(v);Number.isInteger(F)&&F>=M.v&&c(M,F+1)}zl(l)}return!0},ownKeys(d){r(l);var v=Reflect.ownKeys(d).filter(k=>{var C=a.get(k);return C===void 0||C.v!==zr});for(var[x,g]of a)g.v!==zr&&!(x in d)&&v.push(x);return v},setPrototypeOf(){fc()}})}function Fi(e){try{if(e!==null&&typeof e=="object"&&Ra in e)return e[Ra]}catch{}return e}function Zc(e,t){return Object.is(Fi(e),Fi(t))}var ni,Hs,Us,Ws;function eu(){if(ni===void 0){ni=window,Hs=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,a=Text.prototype;Us=cn(t,"firstChild").get,Ws=cn(t,"nextSibling").get,Di(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Di(a)&&(a.__t=void 0)}}function Da(e=""){return document.createTextNode(e)}function Wa(e){return Us.call(e)}function Rl(e){return Ws.call(e)}function i(e,t){return Wa(e)}function te(e,t=!1){{var a=Wa(e);return a instanceof Comment&&a.data===""?Rl(a):a}}function f(e,t=1,a=!1){let n=e;for(;t--;)n=Rl(n);return n}function tu(e){e.textContent=""}function Ks(){return!1}function wi(e,t,a){return document.createElementNS(t??zs,e,void 0)}function ru(e,t){if(t){const a=document.body;e.autofocus=!0,ja(()=>{document.activeElement===a&&e.focus()})}}let Bi=!1;function au(){Bi||(Bi=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const a of e.target.elements)(t=a.__on_r)==null||t.call(a)})},{capture:!0}))}function go(e){var t=ft,a=pt;ua(null),va(null);try{return e()}finally{ua(t),va(a)}}function Ys(e,t,a,n=a){e.addEventListener(t,()=>go(a));const l=e.__on_r;l?e.__on_r=()=>{l(),n(!0)}:e.__on_r=()=>n(!0),au()}function Js(e){pt===null&&(ft===null&&dc(),sc()),mn&&ic()}function nu(e,t){var a=t.last;a===null?t.last=t.first=e:(a.next=e,e.prev=a,t.last=e)}function Ea(e,t){var a=pt;a!==null&&(a.f&Hr)!==0&&(e|=Hr);var n={ctx:Ar,deps:null,nodes:null,f:e|Rr|da,first:null,fn:t,last:null,next:null,parent:a,b:a&&a.b,prev:null,teardown:null,wv:0,ac:null},l=n;if((e&ul)!==0)sl!==null?sl.push(n):La(n);else if(t!==null){try{cl(n)}catch(s){throw jr(n),s}l.deps===null&&l.teardown===null&&l.nodes===null&&l.first===l.last&&(l.f&fl)===0&&(l=l.first,(e&bn)!==0&&(e&Ka)!==0&&l!==null&&(l.f|=Ka))}if(l!==null&&(l.parent=a,a!==null&&nu(l,a),ft!==null&&(ft.f&Dr)!==0&&(e&Vn)===0)){var o=ft;(o.effects??(o.effects=[])).push(l)}return n}function ki(){return ft!==null&&!wa}function ho(e){const t=Ea(Dn,null);return gr(t,Pr),t.teardown=e,t}function na(e){Js();var t=pt.f,a=!ft&&(t&Sa)!==0&&(t&vl)===0;if(a){var n=Ar;(n.e??(n.e=[])).push(e)}else return Xs(e)}function Xs(e){return Ea(ul|ks,e)}function lu(e){return Js(),Ea(Dn|ks,e)}function ou(e){vn.ensure();const t=Ea(Vn|fl,e);return(a={})=>new Promise(n=>{a.outro?In(t,()=>{jr(t),n(void 0)}):(jr(t),n(void 0))})}function _o(e){return Ea(ul,e)}function iu(e){return Ea(gi|fl,e)}function Ci(e,t=0){return Ea(Dn|t,e)}function N(e,t=[],a=[],n=[]){$s(n,t,a,l=>{Ea(Dn,()=>e(...l.map(r)))})}function pl(e,t=0){var a=Ea(bn|t,e);return a}function Qs(e,t=0){var a=Ea(mo|t,e);return a}function Jr(e){return Ea(Sa|fl,e)}function Zs(e){var t=e.teardown;if(t!==null){const a=mn,n=ft;Vi(!0),ua(null);try{t.call(null)}finally{Vi(a),ua(n)}}}function Si(e,t=!1){var a=e.first;for(e.first=e.last=null;a!==null;){const l=a.ac;l!==null&&go(()=>{l.abort(Cn)});var n=a.next;(a.f&Vn)!==0?a.parent=null:jr(a,t),a=n}}function su(e){for(var t=e.first;t!==null;){var a=t.next;(t.f&Sa)===0&&jr(t),t=a}}function jr(e,t=!0){var a=!1;(t||(e.f&ac)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(ed(e.nodes.start,e.nodes.end),a=!0),Si(e,t&&!a),Al(e,0),gr(e,Pa);var n=e.nodes&&e.nodes.t;if(n!==null)for(const o of n)o.stop();Zs(e);var l=e.parent;l!==null&&l.first!==null&&td(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function ed(e,t){for(;e!==null;){var a=e===t?null:Rl(e);e.remove(),e=a}}function td(e){var t=e.parent,a=e.prev,n=e.next;a!==null&&(a.next=n),n!==null&&(n.prev=a),t!==null&&(t.first===e&&(t.first=n),t.last===e&&(t.last=a))}function In(e,t,a=!0){var n=[];rd(e,n,!0);var l=()=>{a&&jr(e),t&&t()},o=n.length;if(o>0){var s=()=>--o||l();for(var d of n)d.out(s)}else l()}function rd(e,t,a){if((e.f&Hr)===0){e.f^=Hr;var n=e.nodes&&e.nodes.t;if(n!==null)for(const d of n)(d.is_global||a)&&t.push(d);for(var l=e.first;l!==null;){var o=l.next,s=(l.f&Ka)!==0||(l.f&Sa)!==0&&(e.f&bn)!==0;rd(l,t,s?a:!1),l=o}}}function Ei(e){ad(e,!0)}function ad(e,t){if((e.f&Hr)!==0){e.f^=Hr;for(var a=e.first;a!==null;){var n=a.next,l=(a.f&Ka)!==0||(a.f&Sa)!==0;ad(a,l?t:!1),a=n}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function Mi(e,t){if(e.nodes)for(var a=e.nodes.start,n=e.nodes.end;a!==null;){var l=a===n?null:Rl(a);t.append(a),a=l}}let ao=!1,mn=!1;function Vi(e){mn=e}let ft=null,wa=!1;function ua(e){ft=e}let pt=null;function va(e){pt=e}let ca=null;function nd(e){ft!==null&&(ca===null?ca=[e]:ca.push(e))}let Yr=null,ta=0,oa=null;function du(e){oa=e}let ld=1,En=0,Ln=En;function Gi(e){Ln=e}function od(){return++ld}function jl(e){var t=e.f;if((t&Rr)!==0)return!0;if(t&Dr&&(e.f&=~qn),(t&Ca)!==0){for(var a=e.deps,n=a.length,l=0;l<n;l++){var o=a[l];if(jl(o)&&Fs(o),o.wv>e.wv)return!0}(t&da)!==0&&Lr===null&&gr(e,Pr)}return!1}function id(e,t,a=!0){var n=e.reactions;if(n!==null&&!(ca!==null&&ol.call(ca,e)))for(var l=0;l<n.length;l++){var o=n[l];(o.f&Dr)!==0?id(o,t,!1):t===o&&(a?gr(o,Rr):(o.f&Pr)!==0&&gr(o,Ca),La(o))}}function sd(e){var I;var t=Yr,a=ta,n=oa,l=ft,o=ca,s=Ar,d=wa,v=Ln,x=e.f;Yr=null,ta=0,oa=null,ft=(x&(Sa|Vn))===0?e:null,ca=null,il(e.ctx),wa=!1,Ln=++En,e.ac!==null&&(go(()=>{e.ac.abort(Cn)}),e.ac=null);try{e.f|=Yo;var g=e.fn,k=g();e.f|=vl;var C=e.deps,R=Ke==null?void 0:Ke.is_fork;if(Yr!==null){var T;if(R||Al(e,ta),C!==null&&ta>0)for(C.length=ta+Yr.length,T=0;T<Yr.length;T++)C[ta+T]=Yr[T];else e.deps=C=Yr;if(ki()&&(e.f&da)!==0)for(T=ta;T<C.length;T++)((I=C[T]).reactions??(I.reactions=[])).push(e)}else!R&&C!==null&&ta<C.length&&(Al(e,ta),C.length=ta);if(Ll()&&oa!==null&&!wa&&C!==null&&(e.f&(Dr|Ca|Rr))===0)for(T=0;T<oa.length;T++)id(oa[T],e);if(l!==null&&l!==e){if(En++,l.deps!==null)for(let y=0;y<a;y+=1)l.deps[y].rv=En;if(t!==null)for(const y of t)y.rv=En;oa!==null&&(n===null?n=oa:n.push(...oa))}return(e.f&un)!==0&&(e.f^=un),k}catch(y){return Is(y)}finally{e.f^=Yo,Yr=t,ta=a,oa=n,ft=l,ca=o,il(s),wa=d,Ln=v}}function cu(e,t){let a=t.reactions;if(a!==null){var n=Xd.call(a,e);if(n!==-1){var l=a.length-1;l===0?a=t.reactions=null:(a[n]=a[l],a.pop())}}if(a===null&&(t.f&Dr)!==0&&(Yr===null||!ol.call(Yr,t))){var o=t;(o.f&da)!==0&&(o.f^=da,o.f&=~qn),hi(o),Jc(o),Al(o,0)}}function Al(e,t){var a=e.deps;if(a!==null)for(var n=t;n<a.length;n++)cu(e,a[n])}function cl(e){var t=e.f;if((t&Pa)===0){gr(e,Pr);var a=pt,n=ao;pt=e,ao=!0;try{(t&(bn|mo))!==0?su(e):Si(e),Zs(e);var l=sd(e);e.teardown=typeof l=="function"?l:null,e.wv=ld;var o;Uo&&Nc&&(e.f&Rr)!==0&&e.deps}finally{ao=n,pt=a}}}async function uu(){await Promise.resolve(),Rc()}function r(e){var t=e.f,a=(t&Dr)!==0;if(ft!==null&&!wa){var n=pt!==null&&(pt.f&Pa)!==0;if(!n&&(ca===null||!ol.call(ca,e))){var l=ft.deps;if((ft.f&Yo)!==0)e.rv<En&&(e.rv=En,Yr===null&&l!==null&&l[ta]===e?ta++:Yr===null?Yr=[e]:Yr.push(e));else{(ft.deps??(ft.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[ft]:ol.call(o,ft)||o.push(ft)}}}if(mn&&fn.has(e))return fn.get(e);if(a){var s=e;if(mn){var d=s.v;return((s.f&Pr)===0&&s.reactions!==null||cd(s))&&(d=yi(s)),fn.set(s,d),d}var v=(s.f&da)===0&&!wa&&ft!==null&&(ao||(ft.f&da)!==0),x=(s.f&vl)===0;jl(s)&&(v&&(s.f|=da),Fs(s)),v&&!x&&(Bs(s),dd(s))}if(Lr!=null&&Lr.has(e))return Lr.get(e);if((e.f&un)!==0)throw e.v;return e.v}function dd(e){if(e.f|=da,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Dr)!==0&&(t.f&da)===0&&(Bs(t),dd(t))}function cd(e){if(e.v===zr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(fn.has(t)||(t.f&Dr)!==0&&cd(t))return!0;return!1}function $n(e){var t=wa;try{return wa=!0,e()}finally{wa=t}}function kn(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Ra in e)li(e);else if(!Array.isArray(e))for(let t in e){const a=e[t];typeof a=="object"&&a&&Ra in a&&li(a)}}}function li(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let n in e)try{li(e[n],t)}catch{}const a=bi(e);if(a!==Object.prototype&&a!==Array.prototype&&a!==Map.prototype&&a!==Set.prototype&&a!==Date.prototype){const n=ys(a);for(let l in n){const o=n[l].get;if(o)try{o.call(e)}catch{}}}}}function vu(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const fu=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function pu(e){return fu.includes(e)}const xu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function mu(e){return e=e.toLowerCase(),xu[e]??e}const bu=["touchstart","touchmove"];function gu(e){return bu.includes(e)}const Mn=Symbol("events"),ud=new Set,oi=new Set;function vd(e,t,a,n={}){function l(o){if(n.capture||ii.call(t,o),!o.cancelBubble)return go(()=>a==null?void 0:a.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?ja(()=>{t.addEventListener(e,l,n)}):t.addEventListener(e,l,n),l}function io(e,t,a,n,l){var o={capture:n,passive:l},s=vd(e,t,a,o);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&ho(()=>{t.removeEventListener(e,s,o)})}function $(e,t,a){(t[Mn]??(t[Mn]={}))[e]=a}function Ya(e){for(var t=0;t<e.length;t++)ud.add(e[t]);for(var a of oi)a(e)}let Hi=null;function ii(e){var y,M;var t=this,a=t.ownerDocument,n=e.type,l=((y=e.composedPath)==null?void 0:y.call(e))||[],o=l[0]||e.target;Hi=e;var s=0,d=Hi===e&&e[Mn];if(d){var v=l.indexOf(d);if(v!==-1&&(t===document||t===window)){e[Mn]=t;return}var x=l.indexOf(t);if(x===-1)return;v<=x&&(s=v)}if(o=l[s]||e.target,o!==t){Qd(e,"currentTarget",{configurable:!0,get(){return o||a}});var g=ft,k=pt;ua(null),va(null);try{for(var C,R=[];o!==null;){var T=o.assignedSlot||o.parentNode||o.host||null;try{var I=(M=o[Mn])==null?void 0:M[n];I!=null&&(!o.disabled||e.target===o)&&I.call(o,e)}catch(F){C?R.push(F):C=F}if(e.cancelBubble||T===t||T===null)break;o=T}if(C){for(let F of R)queueMicrotask(()=>{throw F});throw C}}finally{e[Mn]=t,delete e.currentTarget,ua(g),va(k)}}}var hs;const qo=((hs=globalThis==null?void 0:globalThis.window)==null?void 0:hs.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function hu(e){return(qo==null?void 0:qo.createHTML(e))??e}function fd(e){var t=wi("template");return t.innerHTML=hu(e.replaceAll("<!>","<!---->")),t.content}function Fn(e,t){var a=pt;a.nodes===null&&(a.nodes={start:e,end:t,a:null,t:null})}function m(e,t){var a=(t&Cc)!==0,n=(t&Sc)!==0,l,o=!e.startsWith("<!>");return()=>{l===void 0&&(l=fd(o?e:"<!>"+e),a||(l=Wa(l)));var s=n||Hs?document.importNode(l,!0):l.cloneNode(!0);if(a){var d=Wa(s),v=s.lastChild;Fn(d,v)}else Fn(s,s);return s}}function _u(e,t,a="svg"){var n=!e.startsWith("<!>"),l=`<${a}>${n?e:"<!>"+e}</${a}>`,o;return()=>{if(!o){var s=fd(l),d=Wa(s);o=Wa(d)}var v=o.cloneNode(!0);return Fn(v,v),v}}function yu(e,t){return _u(e,t,"svg")}function sa(e=""){{var t=Da(e+"");return Fn(t,t),t}}function Me(){var e=document.createDocumentFragment(),t=document.createComment(""),a=Da();return e.append(t,a),Fn(t,a),e}function p(e,t){e!==null&&e.before(t)}function S(e,t){var a=t==null?"":typeof t=="object"?`${t}`:t;a!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=a,e.nodeValue=`${a}`)}function wu(e,t){return ku(e,t)}const Xl=new Map;function ku(e,{target:t,anchor:a,props:n={},events:l,context:o,intro:s=!0,transformError:d}){eu();var v=void 0,x=ou(()=>{var g=a??t.appendChild(Da());$c(g,{pending:()=>{}},R=>{fa({});var T=Ar;o&&(T.c=o),l&&(n.$$events=l),v=e(R,n)||{},pa()},d);var k=new Set,C=R=>{for(var T=0;T<R.length;T++){var I=R[T];if(!k.has(I)){k.add(I);var y=gu(I);for(const H of[t,document]){var M=Xl.get(H);M===void 0&&(M=new Map,Xl.set(H,M));var F=M.get(I);F===void 0?(H.addEventListener(I,ii,{passive:y}),M.set(I,1)):M.set(I,F+1)}}}};return C(xo(ud)),oi.add(C),()=>{var y;for(var R of k)for(const M of[t,document]){var T=Xl.get(M),I=T.get(R);--I==0?(M.removeEventListener(R,ii),T.delete(R),T.size===0&&Xl.delete(M)):T.set(R,I)}oi.delete(C),g!==a&&((y=g.parentNode)==null||y.removeChild(g))}});return Cu.set(v,x),v}let Cu=new WeakMap;var ya,Oa,aa,On,Nl,Ol,po;class yo{constructor(t,a=!0){ga(this,"anchor");xt(this,ya,new Map);xt(this,Oa,new Map);xt(this,aa,new Map);xt(this,On,new Set);xt(this,Nl,!0);xt(this,Ol,t=>{if(O(this,ya).has(t)){var a=O(this,ya).get(t),n=O(this,Oa).get(a);if(n)Ei(n),O(this,On).delete(a);else{var l=O(this,aa).get(a);l&&(l.effect.f&Hr)===0&&(O(this,Oa).set(a,l.effect),O(this,aa).delete(a),l.fragment.lastChild.remove(),this.anchor.before(l.fragment),n=l.effect)}for(const[o,s]of O(this,ya)){if(O(this,ya).delete(o),o===t)break;const d=O(this,aa).get(s);d&&(jr(d.effect),O(this,aa).delete(s))}for(const[o,s]of O(this,Oa)){if(o===a||O(this,On).has(o)||(s.f&Hr)!==0)continue;const d=()=>{if(Array.from(O(this,ya).values()).includes(o)){var x=document.createDocumentFragment();Mi(s,x),x.append(Da()),O(this,aa).set(o,{effect:s,fragment:x})}else jr(s);O(this,On).delete(o),O(this,Oa).delete(o)};O(this,Nl)||!n?(O(this,On).add(o),In(s,d,!1)):d()}}});xt(this,po,t=>{O(this,ya).delete(t);const a=Array.from(O(this,ya).values());for(const[n,l]of O(this,aa))a.includes(n)||(jr(l.effect),O(this,aa).delete(n))});this.anchor=t,st(this,Nl,a)}ensure(t,a){var n=Ke,l=Ks();if(a&&!O(this,Oa).has(t)&&!O(this,aa).has(t))if(l){var o=document.createDocumentFragment(),s=Da();o.append(s),O(this,aa).set(t,{effect:Jr(()=>a(s)),fragment:o})}else O(this,Oa).set(t,Jr(()=>a(this.anchor)));if(O(this,ya).set(n,t),l){for(const[d,v]of O(this,Oa))d===t?n.unskip_effect(v):n.skip_effect(v);for(const[d,v]of O(this,aa))d===t?n.unskip_effect(v.effect):n.skip_effect(v.effect);n.oncommit(O(this,Ol)),n.ondiscard(O(this,po))}else O(this,Ol).call(this,n)}}ya=new WeakMap,Oa=new WeakMap,aa=new WeakMap,On=new WeakMap,Nl=new WeakMap,Ol=new WeakMap,po=new WeakMap;function A(e,t,a=!1){var n=new yo(e),l=a?Ka:0;function o(s,d){n.ensure(s,d)}pl(()=>{var s=!1;t((d,v=0)=>{s=!0,o(v,d)}),s||o(-1,null)},l)}function ye(e,t){return t}function Su(e,t,a){for(var n=[],l=t.length,o,s=t.length,d=0;d<l;d++){let k=t[d];In(k,()=>{if(o){if(o.pending.delete(k),o.done.add(k),o.pending.size===0){var C=e.outrogroups;si(e,xo(o.done)),C.delete(o),C.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var v=n.length===0&&a!==null;if(v){var x=a,g=x.parentNode;tu(g),g.append(x),e.items.clear()}si(e,t,!v)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function si(e,t,a=!0){var n;if(e.pending.size>0){n=new Set;for(const s of e.pending.values())for(const d of s)n.add(e.items.get(d).e)}for(var l=0;l<t.length;l++){var o=t[l];if(n!=null&&n.has(o)){o.f|=Ia;const s=document.createDocumentFragment();Mi(o,s)}else jr(t[l],a)}}var Ui;function we(e,t,a,n,l,o=null){var s=e,d=new Map,v=(t&Es)!==0;if(v){var x=e;s=x.appendChild(Da())}var g=null,k=_i(()=>{var H=a();return mi(H)?H:H==null?[]:xo(H)}),C,R=new Map,T=!0;function I(H){(F.effect.f&Pa)===0&&(F.pending.delete(H),F.fallback=g,Eu(F,C,s,t,n),g!==null&&(C.length===0?(g.f&Ia)===0?Ei(g):(g.f^=Ia,Sl(g,null,s)):In(g,()=>{g=null})))}function y(H){F.pending.delete(H)}var M=pl(()=>{C=r(k);for(var H=C.length,_=new Set,L=Ke,U=Ks(),re=0;re<H;re+=1){var E=C[re],Y=n(E,re),X=T?null:d.get(Y);X?(X.v&&dl(X.v,E),X.i&&dl(X.i,re),U&&L.unskip_effect(X.e)):(X=Mu(d,T?s:Ui??(Ui=Da()),E,Y,re,l,t,a),T||(X.e.f|=Ia),d.set(Y,X)),_.add(Y)}if(H===0&&o&&!g&&(T?g=Jr(()=>o(s)):(g=Jr(()=>o(Ui??(Ui=Da()))),g.f|=Ia)),H>_.size&&oc(),!T)if(R.set(L,_),U){for(const[Ce,lt]of d)_.has(Ce)||L.skip_effect(lt.e);L.oncommit(I),L.ondiscard(y)}else I(L);r(k)}),F={effect:M,items:d,pending:R,outrogroups:null,fallback:g};T=!1}function yl(e){for(;e!==null&&(e.f&Sa)===0;)e=e.next;return e}function Eu(e,t,a,n,l){var X,Ce,lt,he,fe,W,Ae,ot,ge;var o=(n&gc)!==0,s=t.length,d=e.items,v=yl(e.effect.first),x,g=null,k,C=[],R=[],T,I,y,M;if(o)for(M=0;M<s;M+=1)T=t[M],I=l(T,M),y=d.get(I).e,(y.f&Ia)===0&&((Ce=(X=y.nodes)==null?void 0:X.a)==null||Ce.measure(),(k??(k=new Set)).add(y));for(M=0;M<s;M+=1){if(T=t[M],I=l(T,M),y=d.get(I).e,e.outrogroups!==null)for(const wt of e.outrogroups)wt.pending.delete(y),wt.done.delete(y);if((y.f&Ia)!==0)if(y.f^=Ia,y===v)Sl(y,null,a);else{var F=g?g.next:v;y===e.effect.last&&(e.effect.last=y.prev),y.prev&&(y.prev.next=y.next),y.next&&(y.next.prev=y.prev),rn(e,g,y),rn(e,y,F),Sl(y,F,a),g=y,C=[],R=[],v=yl(g.next);continue}if((y.f&Hr)!==0&&(Ei(y),o&&((he=(lt=y.nodes)==null?void 0:lt.a)==null||he.unfix(),(k??(k=new Set)).delete(y))),y!==v){if(x!==void 0&&x.has(y)){if(C.length<R.length){var H=R[0],_;g=H.prev;var L=C[0],U=C[C.length-1];for(_=0;_<C.length;_+=1)Sl(C[_],H,a);for(_=0;_<R.length;_+=1)x.delete(R[_]);rn(e,L.prev,U.next),rn(e,g,L),rn(e,U,H),v=H,g=U,M-=1,C=[],R=[]}else x.delete(y),Sl(y,v,a),rn(e,y.prev,y.next),rn(e,y,g===null?e.effect.first:g.next),rn(e,g,y),g=y;continue}for(C=[],R=[];v!==null&&v!==y;)(x??(x=new Set)).add(v),R.push(v),v=yl(v.next);if(v===null)continue}(y.f&Ia)===0&&C.push(y),g=y,v=yl(y.next)}if(e.outrogroups!==null){for(const wt of e.outrogroups)wt.pending.size===0&&(si(e,xo(wt.done)),(fe=e.outrogroups)==null||fe.delete(wt));e.outrogroups.size===0&&(e.outrogroups=null)}if(v!==null||x!==void 0){var re=[];if(x!==void 0)for(y of x)(y.f&Hr)===0&&re.push(y);for(;v!==null;)(v.f&Hr)===0&&v!==e.fallback&&re.push(v),v=yl(v.next);var E=re.length;if(E>0){var Y=(n&Es)!==0&&s===0?a:null;if(o){for(M=0;M<E;M+=1)(Ae=(W=re[M].nodes)==null?void 0:W.a)==null||Ae.measure();for(M=0;M<E;M+=1)(ge=(ot=re[M].nodes)==null?void 0:ot.a)==null||ge.fix()}Su(e,re,Y)}}o&&ja(()=>{var wt,ae;if(k!==void 0)for(y of k)(ae=(wt=y.nodes)==null?void 0:wt.a)==null||ae.apply()})}function Mu(e,t,a,n,l,o,s,d){var v=(s&mc)!==0?(s&hc)===0?Xc(a,!1,!1):xn(a):null,x=(s&bc)!==0?xn(l):null;return{v,i:x,e:Jr(()=>(o(t,v??a,x??l,d),()=>{e.delete(n)}))}}function Sl(e,t,a){if(e.nodes)for(var n=e.nodes.start,l=e.nodes.end,o=t&&(t.f&Ia)===0?t.nodes.start:a;n!==null;){var s=Rl(n);if(o.before(n),n===l)return;n=s}}function rn(e,t,a){t===null?e.effect.first=a:t.next=a,a===null?e.effect.last=t:a.prev=t}function Wi(e,t,a=!1,n=!1,l=!1){var o=e,s="";N(()=>{var d=pt;if(s!==(s=t()??"")&&(d.nodes!==null&&(ed(d.nodes.start,d.nodes.end),d.nodes=null),s!=="")){var v=a?Ts:n?Ec:void 0,x=wi(a?"svg":n?"math":"template",v);x.innerHTML=s;var g=a||n?x:x.content;if(Fn(Wa(g),g.lastChild),a||n)for(;Wa(g);)o.before(Wa(g));else o.before(g)}})}function Ye(e,t,a,n,l){var d;var o=(d=t.$$slots)==null?void 0:d[a],s=!1;o===!0&&(o=t.children,s=!0),o===void 0||o(e,s?()=>n:n)}function di(e,t,...a){var n=new yo(e);pl(()=>{const l=t()??null;n.ensure(l,l&&(o=>l(o,...a)))},Ka)}function zu(e,t,a){var n=new yo(e);pl(()=>{var l=t()??null;n.ensure(l,l&&(o=>a(o,l)))},Ka)}function Tu(e,t,a,n,l,o){var s=null,d=e,v=new yo(d,!1);pl(()=>{const x=t()||null;var g=Ts;if(x===null){v.ensure(null,null);return}return v.ensure(x,k=>{if(x){if(s=wi(x,g),Fn(s,s),n){var C=s.appendChild(Da());n(s,C)}pt.nodes.end=s,k.before(s)}}),()=>{}},Ka),ho(()=>{})}function Au(e,t){var a=void 0,n;Qs(()=>{a!==(a=t())&&(n&&(jr(n),n=null),a&&(n=Jr(()=>{_o(()=>a(e))})))})}function pd(e){var t,a,n="";if(typeof e=="string"||typeof e=="number")n+=e;else if(typeof e=="object")if(Array.isArray(e)){var l=e.length;for(t=0;t<l;t++)e[t]&&(a=pd(e[t]))&&(n&&(n+=" "),n+=a)}else for(a in e)e[a]&&(n&&(n+=" "),n+=a);return n}function xd(){for(var e,t,a=0,n="",l=arguments.length;a<l;a++)(e=arguments[a])&&(t=pd(e))&&(n&&(n+=" "),n+=t);return n}function ut(e){return typeof e=="object"?xd(e):e??""}const Ki=[...` 	
\r\f \v\uFEFF`];function Nu(e,t,a){var n=e==null?"":""+e;if(t&&(n=n?n+" "+t:t),a){for(var l of Object.keys(a))if(a[l])n=n?n+" "+l:l;else if(n.length)for(var o=l.length,s=0;(s=n.indexOf(l,s))>=0;){var d=s+o;(s===0||Ki.includes(n[s-1]))&&(d===n.length||Ki.includes(n[d]))?n=(s===0?"":n.substring(0,s))+n.substring(d+1):s=d}}return n===""?null:n}function Yi(e,t=!1){var a=t?" !important;":";",n="";for(var l of Object.keys(e)){var o=e[l];o!=null&&o!==""&&(n+=" "+l+": "+o+a)}return n}function $o(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Ou(e,t){if(t){var a="",n,l;if(Array.isArray(t)?(n=t[0],l=t[1]):n=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,d=!1,v=[];n&&v.push(...Object.keys(n).map($o)),l&&v.push(...Object.keys(l).map($o));var x=0,g=-1;const I=e.length;for(var k=0;k<I;k++){var C=e[k];if(d?C==="/"&&e[k-1]==="*"&&(d=!1):o?o===C&&(o=!1):C==="/"&&e[k+1]==="*"?d=!0:C==='"'||C==="'"?o=C:C==="("?s++:C===")"&&s--,!d&&o===!1&&s===0){if(C===":"&&g===-1)g=k;else if(C===";"||k===I-1){if(g!==-1){var R=$o(e.substring(x,g).trim());if(!v.includes(R)){C!==";"&&k++;var T=e.substring(x,k).trim();a+=" "+T+";"}}x=k+1,g=-1}}}}return n&&(a+=Yi(n)),l&&(a+=Yi(l,!0)),a=a.trim(),a===""?null:a}return e==null?null:String(e)}function Ge(e,t,a,n,l,o){var s=e.__className;if(s!==a||s===void 0){var d=Nu(a,n,o);d==null?e.removeAttribute("class"):t?e.className=d:e.setAttribute("class",d),e.__className=a}else if(o&&l!==o)for(var v in o){var x=!!o[v];(l==null||x!==!!l[v])&&e.classList.toggle(v,x)}return o}function Fo(e,t={},a,n){for(var l in a){var o=a[l];t[l]!==o&&(a[l]==null?e.style.removeProperty(l):e.style.setProperty(l,o,n))}}function so(e,t,a,n){var l=e.__style;if(l!==t){var o=Ou(t,n);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else n&&(Array.isArray(n)?(Fo(e,a==null?void 0:a[0],n[0]),Fo(e,a==null?void 0:a[1],n[1],"important")):Fo(e,a,n));return n}function co(e,t,a=!1){if(e.multiple){if(t==null)return;if(!mi(t))return zc();for(var n of e.options)n.selected=t.includes(Tl(n));return}for(n of e.options){var l=Tl(n);if(Zc(l,t)){n.selected=!0;return}}(!a||t!==void 0)&&(e.selectedIndex=-1)}function md(e){var t=new MutationObserver(()=>{co(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ho(()=>{t.disconnect()})}function Ji(e,t,a=t){var n=new WeakSet,l=!0;Ys(e,"change",o=>{var s=o?"[selected]":":checked",d;if(e.multiple)d=[].map.call(e.querySelectorAll(s),Tl);else{var v=e.querySelector(s)??e.querySelector("option:not([disabled])");d=v&&Tl(v)}a(d),Ke!==null&&n.add(Ke)}),_o(()=>{var o=t();if(e===document.activeElement){var s=oo??Ke;if(n.has(s))return}if(co(e,o,l),l&&o===void 0){var d=e.querySelector(":checked");d!==null&&(o=Tl(d),a(o))}e.__value=o,l=!1}),md(e)}function Tl(e){return"__value"in e?e.__value:e.value}const wl=Symbol("class"),kl=Symbol("style"),bd=Symbol("is custom element"),gd=Symbol("is html"),Iu=Ss?"option":"OPTION",Lu=Ss?"select":"SELECT";function Pu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function ka(e,t,a,n){var l=hd(e);l[t]!==(l[t]=a)&&(t==="loading"&&(e[nc]=a),a==null?e.removeAttribute(t):typeof a!="string"&&_d(e).includes(t)?e[t]=a:e.setAttribute(t,a))}function Ru(e,t,a,n,l=!1,o=!1){var s=hd(e),d=s[bd],v=!s[gd],x=t||{},g=e.nodeName===Iu;for(var k in t)k in a||(a[k]=null);a.class?a.class=ut(a.class):a[wl]&&(a.class=null),a[kl]&&(a.style??(a.style=null));var C=_d(e);for(const _ in a){let L=a[_];if(g&&_==="value"&&L==null){e.value=e.__value="",x[_]=L;continue}if(_==="class"){var R=e.namespaceURI==="http://www.w3.org/1999/xhtml";Ge(e,R,L,n,t==null?void 0:t[wl],a[wl]),x[_]=L,x[wl]=a[wl];continue}if(_==="style"){so(e,L,t==null?void 0:t[kl],a[kl]),x[_]=L,x[kl]=a[kl];continue}var T=x[_];if(!(L===T&&!(L===void 0&&e.hasAttribute(_)))){x[_]=L;var I=_[0]+_[1];if(I!=="$$")if(I==="on"){const U={},re="$$"+_;let E=_.slice(2);var y=pu(E);if(vu(E)&&(E=E.slice(0,-7),U.capture=!0),!y&&T){if(L!=null)continue;e.removeEventListener(E,x[re],U),x[re]=null}if(y)$(E,e,L),Ya([E]);else if(L!=null){let Y=function(X){x[_].call(this,X)};var H=Y;x[re]=vd(E,e,Y,U)}}else if(_==="style")ka(e,_,L);else if(_==="autofocus")ru(e,!!L);else if(!d&&(_==="__value"||_==="value"&&L!=null))e.value=e.__value=L;else if(_==="selected"&&g)Pu(e,L);else{var M=_;v||(M=mu(M));var F=M==="defaultValue"||M==="defaultChecked";if(L==null&&!d&&!F)if(s[_]=null,M==="value"||M==="checked"){let U=e;const re=t===void 0;if(M==="value"){let E=U.defaultValue;U.removeAttribute(M),U.defaultValue=E,U.value=U.__value=re?E:null}else{let E=U.defaultChecked;U.removeAttribute(M),U.defaultChecked=E,U.checked=re?E:!1}}else e.removeAttribute(_);else F||C.includes(M)&&(d||typeof L!="string")?(e[M]=L,M in s&&(s[M]=zr)):typeof L!="function"&&ka(e,M,L)}}}return x}function uo(e,t,a=[],n=[],l=[],o,s=!1,d=!1){$s(l,a,n,v=>{var x=void 0,g={},k=e.nodeName===Lu,C=!1;if(Qs(()=>{var T=t(...v.map(r)),I=Ru(e,x,T,o,s,d);C&&k&&"value"in T&&co(e,T.value);for(let M of Object.getOwnPropertySymbols(g))T[M]||jr(g[M]);for(let M of Object.getOwnPropertySymbols(T)){var y=T[M];M.description===Mc&&(!x||y!==x[M])&&(g[M]&&jr(g[M]),g[M]=Jr(()=>Au(e,()=>y))),I[M]=y}x=I}),k){var R=e;_o(()=>{co(R,x.value,!0),md(R)})}C=!0})}function hd(e){return e.__attributes??(e.__attributes={[bd]:e.nodeName.includes("-"),[gd]:e.namespaceURI===zs})}var Xi=new Map;function _d(e){var t=e.getAttribute("is")||e.nodeName,a=Xi.get(t);if(a)return a;Xi.set(t,a=[]);for(var n,l=e,o=Element.prototype;o!==l;){n=ys(l);for(var s in n)n[s].set&&a.push(s);l=bi(l)}return a}function Pn(e,t,a=t){var n=new WeakSet;Ys(e,"input",async l=>{var o=l?e.defaultValue:e.value;if(o=Bo(e)?Vo(o):o,a(o),Ke!==null&&n.add(Ke),await uu(),o!==(o=t())){var s=e.selectionStart,d=e.selectionEnd,v=e.value.length;if(e.value=o??"",d!==null){var x=e.value.length;s===d&&d===v&&x>v?(e.selectionStart=x,e.selectionEnd=x):(e.selectionStart=s,e.selectionEnd=Math.min(d,x))}}}),$n(t)==null&&e.value&&(a(Bo(e)?Vo(e.value):e.value),Ke!==null&&n.add(Ke)),Ci(()=>{var l=t();if(e===document.activeElement){var o=oo??Ke;if(n.has(o))return}Bo(e)&&l===Vo(e.value)||e.type==="date"&&!l&&!e.value||l!==e.value&&(e.value=l??"")})}function Bo(e){var t=e.type;return t==="number"||t==="range"}function Vo(e){return e===""?null:+e}function Qi(e,t){return e===t||(e==null?void 0:e[Ra])===t}function pn(e={},t,a,n){return _o(()=>{var l,o;return Ci(()=>{l=o,o=[],$n(()=>{e!==a(...o)&&(t(e,...o),l&&Qi(a(...l),e)&&t(null,...l))})}),()=>{ja(()=>{o&&Qi(a(...o),e)&&t(null,...o)})}}),e}function ju(e=!1){const t=Ar,a=t.l.u;if(!a)return;let n=()=>kn(t.s);if(e){let l=0,o={};const s=Pl(()=>{let d=!1;const v=t.s;for(const x in v)v[x]!==o[x]&&(o[x]=v[x],d=!0);return d&&l++,l});n=()=>r(s)}a.b.length&&lu(()=>{Zi(t,n),Wo(a.b)}),na(()=>{const l=$n(()=>a.m.map(rc));return()=>{for(const o of l)typeof o=="function"&&o()}}),a.a.length&&na(()=>{Zi(t,n),Wo(a.a)})}function Zi(e,t){if(e.l.s)for(const a of e.l.s)r(a);t()}let Ql=!1;function Du(e){var t=Ql;try{return Ql=!1,[e(),Ql]}finally{Ql=t}}const qu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function $u(e,t,a){return new Proxy({props:e,exclude:t},qu)}const Fu={get(e,t){if(!e.exclude.includes(t))return r(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,a){if(!(t in e.special)){var n=pt;try{va(e.parent_effect),e.special[t]=St({get[t](){return e.props[t]}},t,Ms)}finally{va(n)}}return e.special[t](a),Ml(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),Ml(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function He(e,t){return new Proxy({props:e,exclude:t,special:{},version:xn(0),parent_effect:pt},Fu)}const Bu={get(e,t){let a=e.props.length;for(;a--;){let n=e.props[a];if(_l(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n)return n[t]}},set(e,t,a){let n=e.props.length;for(;n--;){let l=e.props[n];_l(l)&&(l=l());const o=cn(l,t);if(o&&o.set)return o.set(a),!0}return!1},getOwnPropertyDescriptor(e,t){let a=e.props.length;for(;a--;){let n=e.props[a];if(_l(n)&&(n=n()),typeof n=="object"&&n!==null&&t in n){const l=cn(n,t);return l&&!l.configurable&&(l.configurable=!0),l}}},has(e,t){if(t===Ra||t===Cs)return!1;for(let a of e.props)if(_l(a)&&(a=a()),a!=null&&t in a)return!0;return!1},ownKeys(e){const t=[];for(let a of e.props)if(_l(a)&&(a=a()),!!a){for(const n in a)t.includes(n)||t.push(n);for(const n of Object.getOwnPropertySymbols(a))t.includes(n)||t.push(n)}return t}};function et(...e){return new Proxy({props:e},Bu)}function St(e,t,a,n){var H;var l=!Il||(a&yc)!==0,o=(a&wc)!==0,s=(a&kc)!==0,d=n,v=!0,x=()=>(v&&(v=!1,d=s?$n(n):n),d),g;if(o){var k=Ra in e||Cs in e;g=((H=cn(e,t))==null?void 0:H.set)??(k&&t in e?_=>e[t]=_:void 0)}var C,R=!1;o?[C,R]=Du(()=>e[t]):C=e[t],C===void 0&&n!==void 0&&(C=x(),g&&(l&&uc(),g(C)));var T;if(l?T=()=>{var _=e[t];return _===void 0?x():(v=!0,_)}:T=()=>{var _=e[t];return _!==void 0&&(d=void 0),_===void 0?d:_},l&&(a&Ms)===0)return T;if(g){var I=e.$$legacy;return(function(_,L){return arguments.length>0?((!l||!L||I||R)&&g(L?T():_),_):T()})}var y=!1,M=((a&_c)!==0?Pl:_i)(()=>(y=!1,T()));o&&r(M);var F=pt;return(function(_,L){if(arguments.length>0){const U=L?r(M):l&&o?yt(_):_;return c(M,U),y=!0,d!==void 0&&(d=U),_}return mn&&y||(F.f&Pa)!==0?M.v:r(M)})}const Vu="5";var _s;typeof window<"u"&&((_s=window.__svelte??(window.__svelte={})).v??(_s.v=new Set)).add(Vu);const qr="";async function Gu(){const e=await fetch(`${qr}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Yn(e,t=null,a=null){const n={provider:e};t&&(n.model=t),a&&(n.api_key=a);const l=await fetch(`${qr}/api/configure`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!l.ok)throw new Error("설정 실패");return l.json()}async function Hu(e){const t=await fetch(`${qr}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function Uu(e,{onProgress:t,onDone:a,onError:n}){const l=new AbortController;return fetch(`${qr}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:l.signal}).then(async o=>{if(!o.ok){n==null||n("다운로드 실패");return}const s=o.body.getReader(),d=new TextDecoder;let v="";for(;;){const{done:x,value:g}=await s.read();if(x)break;v+=d.decode(g,{stream:!0});const k=v.split(`
`);v=k.pop()||"";for(const C of k)if(C.startsWith("data:"))try{const R=JSON.parse(C.slice(5).trim());R.total&&R.completed!==void 0?t==null||t({total:R.total,completed:R.completed,status:R.status}):R.status&&(t==null||t({status:R.status}))}catch{}}a==null||a()}).catch(o=>{o.name!=="AbortError"&&(n==null||n(o.message))}),{abort:()=>l.abort()}}async function Wu(){const e=await fetch(`${qr}/api/oauth/authorize`);if(!e.ok)throw new Error("OAuth 인증 시작 실패");return e.json()}async function Ku(){const e=await fetch(`${qr}/api/oauth/status`);return e.ok?e.json():{done:!1}}async function Yu(){const e=await fetch(`${qr}/api/oauth/logout`,{method:"POST"});if(!e.ok)throw new Error("로그아웃 실패");return e.json()}async function Ju(e,t=null,a=null){let n=`${qr}/api/export/excel/${encodeURIComponent(e)}`;const l=new URLSearchParams;a?l.set("template_id",a):t&&t.length>0&&l.set("modules",t.join(","));const o=l.toString();o&&(n+=`?${o}`);const s=await fetch(n);if(!s.ok){const C=await s.json().catch(()=>({}));throw new Error(C.detail||"Excel 다운로드 실패")}const d=await s.blob(),x=(s.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),g=x?decodeURIComponent(x[1]):`${e}.xlsx`,k=document.createElement("a");return k.href=URL.createObjectURL(d),k.download=g,k.click(),URL.revokeObjectURL(k.href),g}async function Xu(e){const t=await fetch(`${qr}/api/data/sources/${encodeURIComponent(e)}`);if(!t.ok)throw new Error("소스 목록 조회 실패");return t.json()}async function Go(e,t,a=50){const n=new URLSearchParams;a!==50&&n.set("max_rows",String(a));const l=n.toString(),o=`${qr}/api/data/preview/${encodeURIComponent(e)}/${encodeURIComponent(t)}${l?"?"+l:""}`,s=await fetch(o);if(!s.ok){const d=await s.json().catch(()=>({}));throw new Error(d.detail||"미리보기 실패")}return s.json()}async function yd(e){const t=await fetch(`${qr}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function Qu(e){const t=await fetch(`${qr}/api/company/${e}`);if(!t.ok)throw new Error("기업 정보 조회 실패");return t.json()}async function es(e,t,a=null,n=!1){const l=new URLSearchParams;a!==null&&l.set("block",a),n&&l.set("raw","true");const o=l.toString()?`?${l}`:"",s=await fetch(`${qr}/api/company/${e}/show/${encodeURIComponent(t)}${o}`);if(!s.ok)throw new Error("company topic 조회 실패");return s.json()}async function Zu(e){const t=await fetch(`${qr}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}async function ev(e){const t=await fetch(`${qr}/api/company/${e}/diff`);if(!t.ok)throw new Error("diff 조회 실패");return t.json()}async function tv(e,t,a,n){const l=new URLSearchParams({from:a,to:n}),o=await fetch(`${qr}/api/company/${e}/diff/${encodeURIComponent(t)}?${l}`);if(!o.ok)throw new Error("topic diff 조회 실패");return o.json()}function rv(e,t,a={},{onMeta:n,onSnapshot:l,onContext:o,onSystemPrompt:s,onToolCall:d,onToolResult:v,onChunk:x,onDone:g,onError:k},C=null){const R={question:t,stream:!0,...a};e&&(R.company=e),C&&C.length>0&&(R.history=C);const T=new AbortController;return fetch(`${qr}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(R),signal:T.signal}).then(async I=>{if(!I.ok){const L=await I.json().catch(()=>({}));k==null||k(L.detail||"스트리밍 실패");return}const y=I.body.getReader(),M=new TextDecoder;let F="",H=!1,_=null;for(;;){const{done:L,value:U}=await y.read();if(L)break;F+=M.decode(U,{stream:!0});const re=F.split(`
`);F=re.pop()||"";for(const E of re)if(E.startsWith("event:"))_=E.slice(6).trim();else if(E.startsWith("data:")&&_){const Y=E.slice(5).trim();try{const X=JSON.parse(Y);_==="meta"?n==null||n(X):_==="snapshot"?l==null||l(X):_==="context"?o==null||o(X):_==="system_prompt"?s==null||s(X):_==="tool_call"?d==null||d(X):_==="tool_result"?v==null||v(X):_==="chunk"?x==null||x(X.text):_==="error"?k==null||k(X.error,X.action,X.detail):_==="done"&&(H||(H=!0,g==null||g()))}catch{}_=null}}H||(H=!0,g==null||g())}).catch(I=>{I.name!=="AbortError"&&(k==null||k(I.message))}),{abort:()=>T.abort()}}const av=(e,t)=>{const a=new Array(e.length+t.length);for(let n=0;n<e.length;n++)a[n]=e[n];for(let n=0;n<t.length;n++)a[e.length+n]=t[n];return a},nv=(e,t)=>({classGroupId:e,validator:t}),wd=(e=new Map,t=null,a)=>({nextPart:e,validators:t,classGroupId:a}),vo="-",ts=[],lv="arbitrary..",ov=e=>{const t=sv(e),{conflictingClassGroups:a,conflictingClassGroupModifiers:n}=e;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return iv(s);const d=s.split(vo),v=d[0]===""&&d.length>1?1:0;return kd(d,v,t)},getConflictingClassGroupIds:(s,d)=>{if(d){const v=n[s],x=a[s];return v?x?av(x,v):v:x||ts}return a[s]||ts}}},kd=(e,t,a)=>{if(e.length-t===0)return a.classGroupId;const l=e[t],o=a.nextPart.get(l);if(o){const x=kd(e,t+1,o);if(x)return x}const s=a.validators;if(s===null)return;const d=t===0?e.join(vo):e.slice(t).join(vo),v=s.length;for(let x=0;x<v;x++){const g=s[x];if(g.validator(d))return g.classGroupId}},iv=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),a=t.indexOf(":"),n=t.slice(0,a);return n?lv+n:void 0})(),sv=e=>{const{theme:t,classGroups:a}=e;return dv(a,t)},dv=(e,t)=>{const a=wd();for(const n in e){const l=e[n];zi(l,a,n,t)}return a},zi=(e,t,a,n)=>{const l=e.length;for(let o=0;o<l;o++){const s=e[o];cv(s,t,a,n)}},cv=(e,t,a,n)=>{if(typeof e=="string"){uv(e,t,a);return}if(typeof e=="function"){vv(e,t,a,n);return}fv(e,t,a,n)},uv=(e,t,a)=>{const n=e===""?t:Cd(t,e);n.classGroupId=a},vv=(e,t,a,n)=>{if(pv(e)){zi(e(n),t,a,n);return}t.validators===null&&(t.validators=[]),t.validators.push(nv(a,e))},fv=(e,t,a,n)=>{const l=Object.entries(e),o=l.length;for(let s=0;s<o;s++){const[d,v]=l[s];zi(v,Cd(t,d),a,n)}},Cd=(e,t)=>{let a=e;const n=t.split(vo),l=n.length;for(let o=0;o<l;o++){const s=n[o];let d=a.nextPart.get(s);d||(d=wd(),a.nextPart.set(s,d)),a=d}return a},pv=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,xv=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,a=Object.create(null),n=Object.create(null);const l=(o,s)=>{a[o]=s,t++,t>e&&(t=0,n=a,a=Object.create(null))};return{get(o){let s=a[o];if(s!==void 0)return s;if((s=n[o])!==void 0)return l(o,s),s},set(o,s){o in a?a[o]=s:l(o,s)}}},ci="!",rs=":",mv=[],as=(e,t,a,n,l)=>({modifiers:e,hasImportantModifier:t,baseClassName:a,maybePostfixModifierPosition:n,isExternal:l}),bv=e=>{const{prefix:t,experimentalParseClassName:a}=e;let n=l=>{const o=[];let s=0,d=0,v=0,x;const g=l.length;for(let I=0;I<g;I++){const y=l[I];if(s===0&&d===0){if(y===rs){o.push(l.slice(v,I)),v=I+1;continue}if(y==="/"){x=I;continue}}y==="["?s++:y==="]"?s--:y==="("?d++:y===")"&&d--}const k=o.length===0?l:l.slice(v);let C=k,R=!1;k.endsWith(ci)?(C=k.slice(0,-1),R=!0):k.startsWith(ci)&&(C=k.slice(1),R=!0);const T=x&&x>v?x-v:void 0;return as(o,R,C,T)};if(t){const l=t+rs,o=n;n=s=>s.startsWith(l)?o(s.slice(l.length)):as(mv,!1,s,void 0,!0)}if(a){const l=n;n=o=>a({className:o,parseClassName:l})}return n},gv=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((a,n)=>{t.set(a,1e6+n)}),a=>{const n=[];let l=[];for(let o=0;o<a.length;o++){const s=a[o],d=s[0]==="[",v=t.has(s);d||v?(l.length>0&&(l.sort(),n.push(...l),l=[]),n.push(s)):l.push(s)}return l.length>0&&(l.sort(),n.push(...l)),n}},hv=e=>({cache:xv(e.cacheSize),parseClassName:bv(e),sortModifiers:gv(e),...ov(e)}),_v=/\s+/,yv=(e,t)=>{const{parseClassName:a,getClassGroupId:n,getConflictingClassGroupIds:l,sortModifiers:o}=t,s=[],d=e.trim().split(_v);let v="";for(let x=d.length-1;x>=0;x-=1){const g=d[x],{isExternal:k,modifiers:C,hasImportantModifier:R,baseClassName:T,maybePostfixModifierPosition:I}=a(g);if(k){v=g+(v.length>0?" "+v:v);continue}let y=!!I,M=n(y?T.substring(0,I):T);if(!M){if(!y){v=g+(v.length>0?" "+v:v);continue}if(M=n(T),!M){v=g+(v.length>0?" "+v:v);continue}y=!1}const F=C.length===0?"":C.length===1?C[0]:o(C).join(":"),H=R?F+ci:F,_=H+M;if(s.indexOf(_)>-1)continue;s.push(_);const L=l(M,y);for(let U=0;U<L.length;++U){const re=L[U];s.push(H+re)}v=g+(v.length>0?" "+v:v)}return v},wv=(...e)=>{let t=0,a,n,l="";for(;t<e.length;)(a=e[t++])&&(n=Sd(a))&&(l&&(l+=" "),l+=n);return l},Sd=e=>{if(typeof e=="string")return e;let t,a="";for(let n=0;n<e.length;n++)e[n]&&(t=Sd(e[n]))&&(a&&(a+=" "),a+=t);return a},kv=(e,...t)=>{let a,n,l,o;const s=v=>{const x=t.reduce((g,k)=>k(g),e());return a=hv(x),n=a.cache.get,l=a.cache.set,o=d,d(v)},d=v=>{const x=n(v);if(x)return x;const g=yv(v,a);return l(v,g),g};return o=s,(...v)=>o(wv(...v))},Cv=[],kr=e=>{const t=a=>a[e]||Cv;return t.isThemeGetter=!0,t},Ed=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Md=/^\((?:(\w[\w-]*):)?(.+)\)$/i,Sv=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,Ev=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,Mv=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,zv=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Tv=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Av=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,an=e=>Sv.test(e),nt=e=>!!e&&!Number.isNaN(Number(e)),nn=e=>!!e&&Number.isInteger(Number(e)),Ho=e=>e.endsWith("%")&&nt(e.slice(0,-1)),Ga=e=>Ev.test(e),zd=()=>!0,Nv=e=>Mv.test(e)&&!zv.test(e),Ti=()=>!1,Ov=e=>Tv.test(e),Iv=e=>Av.test(e),Lv=e=>!de(e)&&!ue(e),Pv=e=>gn(e,Nd,Ti),de=e=>Ed.test(e),yn=e=>gn(e,Od,Nv),ns=e=>gn(e,Vv,nt),Rv=e=>gn(e,Ld,zd),jv=e=>gn(e,Id,Ti),ls=e=>gn(e,Td,Ti),Dv=e=>gn(e,Ad,Iv),Zl=e=>gn(e,Pd,Ov),ue=e=>Md.test(e),Cl=e=>Gn(e,Od),qv=e=>Gn(e,Id),os=e=>Gn(e,Td),$v=e=>Gn(e,Nd),Fv=e=>Gn(e,Ad),eo=e=>Gn(e,Pd,!0),Bv=e=>Gn(e,Ld,!0),gn=(e,t,a)=>{const n=Ed.exec(e);return n?n[1]?t(n[1]):a(n[2]):!1},Gn=(e,t,a=!1)=>{const n=Md.exec(e);return n?n[1]?t(n[1]):a:!1},Td=e=>e==="position"||e==="percentage",Ad=e=>e==="image"||e==="url",Nd=e=>e==="length"||e==="size"||e==="bg-size",Od=e=>e==="length",Vv=e=>e==="number",Id=e=>e==="family-name",Ld=e=>e==="number"||e==="weight",Pd=e=>e==="shadow",Gv=()=>{const e=kr("color"),t=kr("font"),a=kr("text"),n=kr("font-weight"),l=kr("tracking"),o=kr("leading"),s=kr("breakpoint"),d=kr("container"),v=kr("spacing"),x=kr("radius"),g=kr("shadow"),k=kr("inset-shadow"),C=kr("text-shadow"),R=kr("drop-shadow"),T=kr("blur"),I=kr("perspective"),y=kr("aspect"),M=kr("ease"),F=kr("animate"),H=()=>["auto","avoid","all","avoid-page","page","left","right","column"],_=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],L=()=>[..._(),ue,de],U=()=>["auto","hidden","clip","visible","scroll"],re=()=>["auto","contain","none"],E=()=>[ue,de,v],Y=()=>[an,"full","auto",...E()],X=()=>[nn,"none","subgrid",ue,de],Ce=()=>["auto",{span:["full",nn,ue,de]},nn,ue,de],lt=()=>[nn,"auto",ue,de],he=()=>["auto","min","max","fr",ue,de],fe=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],W=()=>["start","end","center","stretch","center-safe","end-safe"],Ae=()=>["auto",...E()],ot=()=>[an,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...E()],ge=()=>[an,"screen","full","dvw","lvw","svw","min","max","fit",...E()],wt=()=>[an,"screen","full","lh","dvh","lvh","svh","min","max","fit",...E()],ae=()=>[e,ue,de],qt=()=>[..._(),os,ls,{position:[ue,de]}],Ne=()=>["no-repeat",{repeat:["","x","y","space","round"]}],h=()=>["auto","cover","contain",$v,Pv,{size:[ue,de]}],P=()=>[Ho,Cl,yn],B=()=>["","none","full",x,ue,de],Q=()=>["",nt,Cl,yn],pe=()=>["solid","dashed","dotted","double"],xe=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],le=()=>[nt,Ho,os,ls],ct=()=>["","none",T,ue,de],Et=()=>["none",nt,ue,de],Je=()=>["none",nt,ue,de],ze=()=>[nt,ue,de],Mt=()=>[an,"full",...E()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Ga],breakpoint:[Ga],color:[zd],container:[Ga],"drop-shadow":[Ga],ease:["in","out","in-out"],font:[Lv],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Ga],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Ga],shadow:[Ga],spacing:["px",nt],text:[Ga],"text-shadow":[Ga],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",an,de,ue,y]}],container:["container"],columns:[{columns:[nt,de,ue,d]}],"break-after":[{"break-after":H()}],"break-before":[{"break-before":H()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:L()}],overflow:[{overflow:U()}],"overflow-x":[{"overflow-x":U()}],"overflow-y":[{"overflow-y":U()}],overscroll:[{overscroll:re()}],"overscroll-x":[{"overscroll-x":re()}],"overscroll-y":[{"overscroll-y":re()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:Y()}],"inset-x":[{"inset-x":Y()}],"inset-y":[{"inset-y":Y()}],start:[{"inset-s":Y(),start:Y()}],end:[{"inset-e":Y(),end:Y()}],"inset-bs":[{"inset-bs":Y()}],"inset-be":[{"inset-be":Y()}],top:[{top:Y()}],right:[{right:Y()}],bottom:[{bottom:Y()}],left:[{left:Y()}],visibility:["visible","invisible","collapse"],z:[{z:[nn,"auto",ue,de]}],basis:[{basis:[an,"full","auto",d,...E()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[nt,an,"auto","initial","none",de]}],grow:[{grow:["",nt,ue,de]}],shrink:[{shrink:["",nt,ue,de]}],order:[{order:[nn,"first","last","none",ue,de]}],"grid-cols":[{"grid-cols":X()}],"col-start-end":[{col:Ce()}],"col-start":[{"col-start":lt()}],"col-end":[{"col-end":lt()}],"grid-rows":[{"grid-rows":X()}],"row-start-end":[{row:Ce()}],"row-start":[{"row-start":lt()}],"row-end":[{"row-end":lt()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":he()}],"auto-rows":[{"auto-rows":he()}],gap:[{gap:E()}],"gap-x":[{"gap-x":E()}],"gap-y":[{"gap-y":E()}],"justify-content":[{justify:[...fe(),"normal"]}],"justify-items":[{"justify-items":[...W(),"normal"]}],"justify-self":[{"justify-self":["auto",...W()]}],"align-content":[{content:["normal",...fe()]}],"align-items":[{items:[...W(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...W(),{baseline:["","last"]}]}],"place-content":[{"place-content":fe()}],"place-items":[{"place-items":[...W(),"baseline"]}],"place-self":[{"place-self":["auto",...W()]}],p:[{p:E()}],px:[{px:E()}],py:[{py:E()}],ps:[{ps:E()}],pe:[{pe:E()}],pbs:[{pbs:E()}],pbe:[{pbe:E()}],pt:[{pt:E()}],pr:[{pr:E()}],pb:[{pb:E()}],pl:[{pl:E()}],m:[{m:Ae()}],mx:[{mx:Ae()}],my:[{my:Ae()}],ms:[{ms:Ae()}],me:[{me:Ae()}],mbs:[{mbs:Ae()}],mbe:[{mbe:Ae()}],mt:[{mt:Ae()}],mr:[{mr:Ae()}],mb:[{mb:Ae()}],ml:[{ml:Ae()}],"space-x":[{"space-x":E()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":E()}],"space-y-reverse":["space-y-reverse"],size:[{size:ot()}],"inline-size":[{inline:["auto",...ge()]}],"min-inline-size":[{"min-inline":["auto",...ge()]}],"max-inline-size":[{"max-inline":["none",...ge()]}],"block-size":[{block:["auto",...wt()]}],"min-block-size":[{"min-block":["auto",...wt()]}],"max-block-size":[{"max-block":["none",...wt()]}],w:[{w:[d,"screen",...ot()]}],"min-w":[{"min-w":[d,"screen","none",...ot()]}],"max-w":[{"max-w":[d,"screen","none","prose",{screen:[s]},...ot()]}],h:[{h:["screen","lh",...ot()]}],"min-h":[{"min-h":["screen","lh","none",...ot()]}],"max-h":[{"max-h":["screen","lh",...ot()]}],"font-size":[{text:["base",a,Cl,yn]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[n,Bv,Rv]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Ho,de]}],"font-family":[{font:[qv,jv,t]}],"font-features":[{"font-features":[de]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[l,ue,de]}],"line-clamp":[{"line-clamp":[nt,"none",ue,ns]}],leading:[{leading:[o,...E()]}],"list-image":[{"list-image":["none",ue,de]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",ue,de]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:ae()}],"text-color":[{text:ae()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...pe(),"wavy"]}],"text-decoration-thickness":[{decoration:[nt,"from-font","auto",ue,yn]}],"text-decoration-color":[{decoration:ae()}],"underline-offset":[{"underline-offset":[nt,"auto",ue,de]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:E()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",ue,de]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",ue,de]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:qt()}],"bg-repeat":[{bg:Ne()}],"bg-size":[{bg:h()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},nn,ue,de],radial:["",ue,de],conic:[nn,ue,de]},Fv,Dv]}],"bg-color":[{bg:ae()}],"gradient-from-pos":[{from:P()}],"gradient-via-pos":[{via:P()}],"gradient-to-pos":[{to:P()}],"gradient-from":[{from:ae()}],"gradient-via":[{via:ae()}],"gradient-to":[{to:ae()}],rounded:[{rounded:B()}],"rounded-s":[{"rounded-s":B()}],"rounded-e":[{"rounded-e":B()}],"rounded-t":[{"rounded-t":B()}],"rounded-r":[{"rounded-r":B()}],"rounded-b":[{"rounded-b":B()}],"rounded-l":[{"rounded-l":B()}],"rounded-ss":[{"rounded-ss":B()}],"rounded-se":[{"rounded-se":B()}],"rounded-ee":[{"rounded-ee":B()}],"rounded-es":[{"rounded-es":B()}],"rounded-tl":[{"rounded-tl":B()}],"rounded-tr":[{"rounded-tr":B()}],"rounded-br":[{"rounded-br":B()}],"rounded-bl":[{"rounded-bl":B()}],"border-w":[{border:Q()}],"border-w-x":[{"border-x":Q()}],"border-w-y":[{"border-y":Q()}],"border-w-s":[{"border-s":Q()}],"border-w-e":[{"border-e":Q()}],"border-w-bs":[{"border-bs":Q()}],"border-w-be":[{"border-be":Q()}],"border-w-t":[{"border-t":Q()}],"border-w-r":[{"border-r":Q()}],"border-w-b":[{"border-b":Q()}],"border-w-l":[{"border-l":Q()}],"divide-x":[{"divide-x":Q()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":Q()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...pe(),"hidden","none"]}],"divide-style":[{divide:[...pe(),"hidden","none"]}],"border-color":[{border:ae()}],"border-color-x":[{"border-x":ae()}],"border-color-y":[{"border-y":ae()}],"border-color-s":[{"border-s":ae()}],"border-color-e":[{"border-e":ae()}],"border-color-bs":[{"border-bs":ae()}],"border-color-be":[{"border-be":ae()}],"border-color-t":[{"border-t":ae()}],"border-color-r":[{"border-r":ae()}],"border-color-b":[{"border-b":ae()}],"border-color-l":[{"border-l":ae()}],"divide-color":[{divide:ae()}],"outline-style":[{outline:[...pe(),"none","hidden"]}],"outline-offset":[{"outline-offset":[nt,ue,de]}],"outline-w":[{outline:["",nt,Cl,yn]}],"outline-color":[{outline:ae()}],shadow:[{shadow:["","none",g,eo,Zl]}],"shadow-color":[{shadow:ae()}],"inset-shadow":[{"inset-shadow":["none",k,eo,Zl]}],"inset-shadow-color":[{"inset-shadow":ae()}],"ring-w":[{ring:Q()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:ae()}],"ring-offset-w":[{"ring-offset":[nt,yn]}],"ring-offset-color":[{"ring-offset":ae()}],"inset-ring-w":[{"inset-ring":Q()}],"inset-ring-color":[{"inset-ring":ae()}],"text-shadow":[{"text-shadow":["none",C,eo,Zl]}],"text-shadow-color":[{"text-shadow":ae()}],opacity:[{opacity:[nt,ue,de]}],"mix-blend":[{"mix-blend":[...xe(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":xe()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[nt]}],"mask-image-linear-from-pos":[{"mask-linear-from":le()}],"mask-image-linear-to-pos":[{"mask-linear-to":le()}],"mask-image-linear-from-color":[{"mask-linear-from":ae()}],"mask-image-linear-to-color":[{"mask-linear-to":ae()}],"mask-image-t-from-pos":[{"mask-t-from":le()}],"mask-image-t-to-pos":[{"mask-t-to":le()}],"mask-image-t-from-color":[{"mask-t-from":ae()}],"mask-image-t-to-color":[{"mask-t-to":ae()}],"mask-image-r-from-pos":[{"mask-r-from":le()}],"mask-image-r-to-pos":[{"mask-r-to":le()}],"mask-image-r-from-color":[{"mask-r-from":ae()}],"mask-image-r-to-color":[{"mask-r-to":ae()}],"mask-image-b-from-pos":[{"mask-b-from":le()}],"mask-image-b-to-pos":[{"mask-b-to":le()}],"mask-image-b-from-color":[{"mask-b-from":ae()}],"mask-image-b-to-color":[{"mask-b-to":ae()}],"mask-image-l-from-pos":[{"mask-l-from":le()}],"mask-image-l-to-pos":[{"mask-l-to":le()}],"mask-image-l-from-color":[{"mask-l-from":ae()}],"mask-image-l-to-color":[{"mask-l-to":ae()}],"mask-image-x-from-pos":[{"mask-x-from":le()}],"mask-image-x-to-pos":[{"mask-x-to":le()}],"mask-image-x-from-color":[{"mask-x-from":ae()}],"mask-image-x-to-color":[{"mask-x-to":ae()}],"mask-image-y-from-pos":[{"mask-y-from":le()}],"mask-image-y-to-pos":[{"mask-y-to":le()}],"mask-image-y-from-color":[{"mask-y-from":ae()}],"mask-image-y-to-color":[{"mask-y-to":ae()}],"mask-image-radial":[{"mask-radial":[ue,de]}],"mask-image-radial-from-pos":[{"mask-radial-from":le()}],"mask-image-radial-to-pos":[{"mask-radial-to":le()}],"mask-image-radial-from-color":[{"mask-radial-from":ae()}],"mask-image-radial-to-color":[{"mask-radial-to":ae()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":_()}],"mask-image-conic-pos":[{"mask-conic":[nt]}],"mask-image-conic-from-pos":[{"mask-conic-from":le()}],"mask-image-conic-to-pos":[{"mask-conic-to":le()}],"mask-image-conic-from-color":[{"mask-conic-from":ae()}],"mask-image-conic-to-color":[{"mask-conic-to":ae()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:qt()}],"mask-repeat":[{mask:Ne()}],"mask-size":[{mask:h()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",ue,de]}],filter:[{filter:["","none",ue,de]}],blur:[{blur:ct()}],brightness:[{brightness:[nt,ue,de]}],contrast:[{contrast:[nt,ue,de]}],"drop-shadow":[{"drop-shadow":["","none",R,eo,Zl]}],"drop-shadow-color":[{"drop-shadow":ae()}],grayscale:[{grayscale:["",nt,ue,de]}],"hue-rotate":[{"hue-rotate":[nt,ue,de]}],invert:[{invert:["",nt,ue,de]}],saturate:[{saturate:[nt,ue,de]}],sepia:[{sepia:["",nt,ue,de]}],"backdrop-filter":[{"backdrop-filter":["","none",ue,de]}],"backdrop-blur":[{"backdrop-blur":ct()}],"backdrop-brightness":[{"backdrop-brightness":[nt,ue,de]}],"backdrop-contrast":[{"backdrop-contrast":[nt,ue,de]}],"backdrop-grayscale":[{"backdrop-grayscale":["",nt,ue,de]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[nt,ue,de]}],"backdrop-invert":[{"backdrop-invert":["",nt,ue,de]}],"backdrop-opacity":[{"backdrop-opacity":[nt,ue,de]}],"backdrop-saturate":[{"backdrop-saturate":[nt,ue,de]}],"backdrop-sepia":[{"backdrop-sepia":["",nt,ue,de]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":E()}],"border-spacing-x":[{"border-spacing-x":E()}],"border-spacing-y":[{"border-spacing-y":E()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",ue,de]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[nt,"initial",ue,de]}],ease:[{ease:["linear","initial",M,ue,de]}],delay:[{delay:[nt,ue,de]}],animate:[{animate:["none",F,ue,de]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[I,ue,de]}],"perspective-origin":[{"perspective-origin":L()}],rotate:[{rotate:Et()}],"rotate-x":[{"rotate-x":Et()}],"rotate-y":[{"rotate-y":Et()}],"rotate-z":[{"rotate-z":Et()}],scale:[{scale:Je()}],"scale-x":[{"scale-x":Je()}],"scale-y":[{"scale-y":Je()}],"scale-z":[{"scale-z":Je()}],"scale-3d":["scale-3d"],skew:[{skew:ze()}],"skew-x":[{"skew-x":ze()}],"skew-y":[{"skew-y":ze()}],transform:[{transform:[ue,de,"","none","gpu","cpu"]}],"transform-origin":[{origin:L()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:Mt()}],"translate-x":[{"translate-x":Mt()}],"translate-y":[{"translate-y":Mt()}],"translate-z":[{"translate-z":Mt()}],"translate-none":["translate-none"],accent:[{accent:ae()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:ae()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",ue,de]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":E()}],"scroll-mx":[{"scroll-mx":E()}],"scroll-my":[{"scroll-my":E()}],"scroll-ms":[{"scroll-ms":E()}],"scroll-me":[{"scroll-me":E()}],"scroll-mbs":[{"scroll-mbs":E()}],"scroll-mbe":[{"scroll-mbe":E()}],"scroll-mt":[{"scroll-mt":E()}],"scroll-mr":[{"scroll-mr":E()}],"scroll-mb":[{"scroll-mb":E()}],"scroll-ml":[{"scroll-ml":E()}],"scroll-p":[{"scroll-p":E()}],"scroll-px":[{"scroll-px":E()}],"scroll-py":[{"scroll-py":E()}],"scroll-ps":[{"scroll-ps":E()}],"scroll-pe":[{"scroll-pe":E()}],"scroll-pbs":[{"scroll-pbs":E()}],"scroll-pbe":[{"scroll-pbe":E()}],"scroll-pt":[{"scroll-pt":E()}],"scroll-pr":[{"scroll-pr":E()}],"scroll-pb":[{"scroll-pb":E()}],"scroll-pl":[{"scroll-pl":E()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",ue,de]}],fill:[{fill:["none",...ae()]}],"stroke-w":[{stroke:[nt,Cl,yn,ns]}],stroke:[{stroke:["none",...ae()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Hv=kv(Gv);function vt(...e){return Hv(xd(e))}const ui="dartlab-conversations",is=50;function Uv(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Wv(){try{const e=localStorage.getItem(ui);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const Kv=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function ss(e){return e.map(t=>({...t,messages:t.messages.map(a=>{if(a.role!=="assistant")return a;const n={};for(const[l,o]of Object.entries(a))Kv.includes(l)||(n[l]=o);return n})}))}function ds(e){try{const t={conversations:ss(e.conversations),activeId:e.activeId};localStorage.setItem(ui,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:ss(e.conversations),activeId:e.activeId};localStorage.setItem(ui,JSON.stringify(t))}catch{}}}}function Yv(){const e=Wv(),t=e.conversations||[],a=t.find(M=>M.id===e.activeId)?e.activeId:null;let n=D(yt(t)),l=D(yt(a)),o=null;function s(){o&&clearTimeout(o),o=setTimeout(()=>{ds({conversations:r(n),activeId:r(l)}),o=null},300)}function d(){o&&clearTimeout(o),o=null,ds({conversations:r(n),activeId:r(l)})}function v(){return r(n).find(M=>M.id===r(l))||null}function x(){const M={id:Uv(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return c(n,[M,...r(n)],!0),r(n).length>is&&c(n,r(n).slice(0,is),!0),c(l,M.id,!0),d(),M.id}function g(M){r(n).find(F=>F.id===M)&&(c(l,M,!0),d())}function k(M,F,H=null){const _=v();if(!_)return;const L={role:M,text:F};H&&(L.meta=H),_.messages=[..._.messages,L],_.updatedAt=Date.now(),_.title==="새 대화"&&M==="user"&&(_.title=F.length>30?F.slice(0,30)+"...":F),c(n,[...r(n)],!0),d()}function C(M){const F=v();if(!F||F.messages.length===0)return;const H=F.messages[F.messages.length-1];Object.assign(H,M),F.updatedAt=Date.now(),c(n,[...r(n)],!0),s()}function R(M){c(n,r(n).filter(F=>F.id!==M),!0),r(l)===M&&c(l,r(n).length>0?r(n)[0].id:null,!0),d()}function T(){const M=v();!M||M.messages.length===0||(M.messages=M.messages.slice(0,-1),M.updatedAt=Date.now(),c(n,[...r(n)],!0),d())}function I(M,F){const H=r(n).find(_=>_.id===M);H&&(H.title=F,c(n,[...r(n)],!0),d())}function y(){c(n,[],!0),c(l,null),d()}return{get conversations(){return r(n)},get activeId(){return r(l)},get active(){return v()},createConversation:x,setActive:g,addMessage:k,updateLastMessage:C,removeLastMessage:T,deleteConversation:R,updateTitle:I,clearAll:y,flush:d}}const Rd="dartlab-workspace",Jv=new Set(["sections","overview","explore","evidence"]),Xv=6;function Jn(e){return Jv.has(e)?e:"overview"}function wo(){return typeof window<"u"&&typeof localStorage<"u"}function Qv(){if(!wo())return{};const e=new URLSearchParams(window.location.search),t=e.get("company")||null,a=e.get("tab"),n=e.get("panel");return{stockCode:t,tab:a?Jn(a):null,isOpen:n==="open"?!0:n==="closed"?!1:null}}function Zv(){if(!wo())return{};try{const e=localStorage.getItem(Rd);if(!e)return{};const t=JSON.parse(e);return{isOpen:typeof t.isOpen=="boolean"?t.isOpen:!0,activeTab:Jn(t.activeTab),selectedCompany:t.selectedCompany||null,userPinnedCompany:!!t.userPinnedCompany,recentCompanies:Array.isArray(t.recentCompanies)?t.recentCompanies:[],activeEvidenceSection:t.activeEvidenceSection||null,selectedEvidenceIndex:Number.isInteger(t.selectedEvidenceIndex)?t.selectedEvidenceIndex:null}}catch{return{}}}function ef(e){wo()&&localStorage.setItem(Rd,JSON.stringify(e))}function tf(e){var a;if(!wo())return;const t=new URL(window.location.href);(a=e.selectedCompany)!=null&&a.stockCode?t.searchParams.set("company",e.selectedCompany.stockCode):t.searchParams.delete("company"),t.searchParams.set("tab",Jn(e.activeTab)),t.searchParams.set("panel",e.isOpen?"open":"closed"),window.history.replaceState({},"",t)}function rf(){const e=Zv(),t=Qv(),a=t.stockCode?{...e.selectedCompany||{},stockCode:t.stockCode}:e.selectedCompany||null;let n=D(yt(t.isOpen??e.isOpen??!0)),l=D(yt(t.tab??e.activeTab??"overview")),o=D(yt(a)),s=D(yt(e.userPinnedCompany??!!a)),d=D(yt(e.recentCompanies||[])),v=D(yt(e.activeEvidenceSection??null)),x=D(yt(e.selectedEvidenceIndex??null));function g(_){if(!(_!=null&&_.stockCode))return;const L={stockCode:_.stockCode,corpName:_.corpName||_.company||_.stockCode,company:_.company||_.corpName||_.stockCode,market:_.market||"",sector:_.sector||""},U=r(d).filter(re=>re.stockCode!==L.stockCode);c(d,[L,...U].slice(0,Xv),!0)}function k(){const _={isOpen:r(n),activeTab:r(l),selectedCompany:r(o),userPinnedCompany:r(s),recentCompanies:r(d),activeEvidenceSection:r(v),selectedEvidenceIndex:r(x)};ef(_),tf(_)}function C(_="explore"){c(l,Jn(_),!0),c(n,!0),r(l)!=="evidence"&&(c(v,null),c(x,null)),k()}function R(){c(n,!1),k()}function T(_){c(l,Jn(_),!0),r(l)!=="evidence"&&(c(v,null),c(x,null)),k()}function I(_,L=null){c(l,"evidence"),c(n,!0),c(v,_||null,!0),c(x,Number.isInteger(L)?L:null,!0),k()}function y(){c(v,null),c(x,null),k()}function M(_,{pin:L=!0,openTab:U=null}={}){c(o,_,!0),c(s,_?L:!1,!0),c(v,null),c(x,null),_&&g(_),U&&(c(l,Jn(U),!0),c(n,!0)),k()}function F(_={},L=null){var U,re,E,Y,X;!(_!=null&&_.company)&&!(_!=null&&_.stockCode)||(c(o,{...r(o)||{},...L||{},corpName:_.company||((U=r(o))==null?void 0:U.corpName)||(L==null?void 0:L.corpName)||(L==null?void 0:L.company),company:_.company||((re=r(o))==null?void 0:re.company)||(L==null?void 0:L.company)||(L==null?void 0:L.corpName),stockCode:_.stockCode||((E=r(o))==null?void 0:E.stockCode)||(L==null?void 0:L.stockCode),market:((Y=r(o))==null?void 0:Y.market)||(L==null?void 0:L.market)||"",sector:((X=r(o))==null?void 0:X.sector)||(L==null?void 0:L.sector)||""},!0),c(s,!0),g(r(o)),k())}function H(){c(o,null),c(s,!1),c(v,null),c(x,null),k()}return{get isOpen(){return r(n)},get activeTab(){return r(l)},get selectedCompany(){return r(o)},get userPinnedCompany(){return r(s)},get recentCompanies(){return r(d)},get activeEvidenceSection(){return r(v)},get selectedEvidenceIndex(){return r(x)},open:C,close:R,setTab:T,openEvidence:I,clearEvidenceSelection:y,selectCompany:M,syncCompanyFromMessage:F,resetCompany:H}}var af=m("<a><!></a>"),nf=m("<button><!></button>");function lf(e,t){fa(t,!0);let a=St(t,"variant",3,"default"),n=St(t,"size",3,"default"),l=$u(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const o={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var d=Me(),v=te(d);{var x=k=>{var C=af();uo(C,T=>({class:T,...l}),[()=>vt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",o[a()],s[n()],t.class)]);var R=i(C);di(R,()=>t.children),p(k,C)},g=k=>{var C=nf();uo(C,T=>({class:T,...l}),[()=>vt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",o[a()],s[n()],t.class)]);var R=i(C);di(R,()=>t.children),p(k,C)};A(v,k=>{t.href?k(x):k(g,-1)})}p(e,d),pa()}Oc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const of={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const sf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const cs=(...e)=>e.filter((t,a,n)=>!!t&&t.trim()!==""&&n.indexOf(t)===a).join(" ").trim();var df=yu("<svg><!><!></svg>");function tt(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]),n=He(a,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);fa(t,!1);let l=St(t,"name",8,void 0),o=St(t,"color",8,"currentColor"),s=St(t,"size",8,24),d=St(t,"strokeWidth",8,2),v=St(t,"absoluteStrokeWidth",8,!1),x=St(t,"iconNode",24,()=>[]);ju();var g=df();uo(g,(R,T,I)=>({...of,...R,...n,width:s(),height:s(),stroke:o(),"stroke-width":T,class:I}),[()=>sf(n)?void 0:{"aria-hidden":"true"},()=>(kn(v()),kn(d()),kn(s()),$n(()=>v()?Number(d())*24/Number(s()):d())),()=>(kn(cs),kn(l()),kn(a),$n(()=>cs("lucide-icon","lucide",l()?`lucide-${l()}`:"",a.class)))]);var k=i(g);we(k,1,x,ye,(R,T)=>{var I=se(()=>lo(r(T),2));let y=()=>r(I)[0],M=()=>r(I)[1];var F=Me(),H=te(F);Tu(H,y,!0,(_,L)=>{uo(_,()=>({...M()}))}),p(R,F)});var C=f(k);Ye(C,t,"default",{}),p(e,g),pa()}function cf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];tt(e,et({name:"activity"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function uf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];tt(e,et({name:"arrow-up"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function no(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];tt(e,et({name:"brain"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function vf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M20 6 9 17l-5-5"}]];tt(e,et({name:"check"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function jd(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m6 9 6 6 6-6"}]];tt(e,et({name:"chevron-down"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function vi(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m9 18 6-6-6-6"}]];tt(e,et({name:"chevron-right"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function wn(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];tt(e,et({name:"circle-alert"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Rn(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];tt(e,et({name:"circle-check"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function ff(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];tt(e,et({name:"clock"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function pf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];tt(e,et({name:"code"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function xf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];tt(e,et({name:"coffee"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Cr(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];tt(e,et({name:"database"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function jn(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];tt(e,et({name:"download"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function us(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];tt(e,et({name:"external-link"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function fi(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];tt(e,et({name:"eye"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function zn(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];tt(e,et({name:"file-text"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function mf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];tt(e,et({name:"github"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function vs(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];tt(e,et({name:"key"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function bf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m5 8 6 6"}],["path",{d:"m4 14 6-6 2-3"}],["path",{d:"M2 5h12"}],["path",{d:"M7 2h1"}],["path",{d:"m22 22-5-10-5 10"}],["path",{d:"M14 18h6"}]];tt(e,et({name:"languages"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function gf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9 17H7A5 5 0 0 1 7 7h2"}],["path",{d:"M15 7h2a5 5 0 1 1 0 10h-2"}],["line",{x1:"8",x2:"16",y1:"12",y2:"12"}]];tt(e,et({name:"link-2"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Tr(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];tt(e,et({name:"loader-circle"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function hf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m10 17 5-5-5-5"}],["path",{d:"M15 12H3"}],["path",{d:"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"}]];tt(e,et({name:"log-in"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function _f(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];tt(e,et({name:"log-out"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function yf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];tt(e,et({name:"menu"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function fs(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];tt(e,et({name:"message-square"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function wf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];tt(e,et({name:"panel-left-close"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function ps(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];tt(e,et({name:"plus"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function kf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];tt(e,et({name:"refresh-cw"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Cf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"}],["path",{d:"M3 3v5h5"}]];tt(e,et({name:"rotate-ccw"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Sf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M15 12h-5"}],["path",{d:"M15 8h-5"}],["path",{d:"M19 17V5a2 2 0 0 0-2-2H4"}],["path",{d:"M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"}]];tt(e,et({name:"scroll-text"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Bn(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];tt(e,et({name:"search"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Ef(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];tt(e,et({name:"settings"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Mf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];tt(e,et({name:"sparkles"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function zf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];tt(e,et({name:"square"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function xs(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];tt(e,et({name:"table-2"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Tf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];tt(e,et({name:"terminal"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Af(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];tt(e,et({name:"trash-2"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Nf(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];tt(e,et({name:"triangle-alert"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function pi(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];tt(e,et({name:"wrench"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}function Xn(e,t){const a=He(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const n=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];tt(e,et({name:"x"},()=>a,{get iconNode(){return n},children:(l,o)=>{var s=Me(),d=te(s);Ye(d,t,"default",{}),p(l,s)},$$slots:{default:!0}}))}var Of=m("<!> 새 대화",1),If=m('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Lf=m('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Pf=m('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Rf=m('<div class="flex-shrink-0 px-4 py-3 border-t border-dl-border/40"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Version</div> <div class="mt-1 text-[10px] text-dl-text-muted"> </div></div>'),jf=m('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Df=m("<button><!></button>"),qf=m('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),$f=m("<aside><!></aside>");function Ff(e,t){fa(t,!0);let a=St(t,"conversations",19,()=>[]),n=St(t,"activeId",3,null),l=St(t,"open",3,!0),o=St(t,"version",3,""),s=D("");function d(T){const I=new Date().setHours(0,0,0,0),y=I-864e5,M=I-7*864e5,F={오늘:[],어제:[],"이번 주":[],이전:[]};for(const _ of T)_.updatedAt>=I?F.오늘.push(_):_.updatedAt>=y?F.어제.push(_):_.updatedAt>=M?F["이번 주"].push(_):F.이전.push(_);const H=[];for(const[_,L]of Object.entries(F))L.length>0&&H.push({label:_,items:L});return H}let v=se(()=>r(s).trim()?a().filter(T=>T.title.toLowerCase().includes(r(s).toLowerCase())):a()),x=se(()=>d(r(v)));var g=$f(),k=i(g);{var C=T=>{var I=jf(),y=f(i(I),2),M=i(y);lf(M,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(re,E)=>{var Y=Of(),X=te(Y);ps(X,{size:16}),p(re,Y)},$$slots:{default:!0}});var F=f(y,2);{var H=re=>{var E=If(),Y=i(E),X=i(Y);Bn(X,{size:12,class:"text-dl-text-dim flex-shrink-0"});var Ce=f(X,2);Pn(Ce,()=>r(s),lt=>c(s,lt)),p(re,E)};A(F,re=>{a().length>3&&re(H)})}var _=f(F,2);we(_,21,()=>r(x),ye,(re,E)=>{var Y=Pf(),X=i(Y),Ce=i(X),lt=f(X,2);we(lt,17,()=>r(E).items,ye,(he,fe)=>{var W=Lf(),Ae=i(W),ot=i(Ae);fs(ot,{size:14,class:"flex-shrink-0 opacity-50"});var ge=f(ot,2),wt=i(ge),ae=f(Ae,2),qt=i(ae);Af(qt,{size:12}),N(Ne=>{Ge(W,1,Ne),ka(Ae,"aria-current",r(fe).id===n()?"true":void 0),S(wt,r(fe).title),ka(ae,"aria-label",`${r(fe).title} 삭제`)},[()=>ut(vt("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",r(fe).id===n()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),$("click",Ae,()=>{var Ne;return(Ne=t.onSelect)==null?void 0:Ne.call(t,r(fe).id)}),$("click",ae,Ne=>{var h;Ne.stopPropagation(),(h=t.onDelete)==null||h.call(t,r(fe).id)}),p(he,W)}),N(()=>S(Ce,r(E).label)),p(re,Y)});var L=f(_,2);{var U=re=>{var E=Rf(),Y=f(i(E),2),X=i(Y);N(()=>S(X,`DartLab v${o()??""}`)),p(re,E)};A(L,re=>{o()&&re(U)})}p(T,I)},R=T=>{var I=qf(),y=f(i(I),2),M=i(y);ps(M,{size:18});var F=f(y,2);we(F,21,()=>a().slice(0,10),ye,(H,_)=>{var L=Df(),U=i(L);fs(U,{size:16}),N(re=>{Ge(L,1,re),ka(L,"title",r(_).title)},[()=>ut(vt("p-2 rounded-lg transition-colors w-full flex justify-center",r(_).id===n()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),$("click",L,()=>{var re;return(re=t.onSelect)==null?void 0:re.call(t,r(_).id)}),p(H,L)}),$("click",y,function(...H){var _;(_=t.onNewChat)==null||_.apply(this,H)}),p(T,I)};A(k,T=>{l()?T(C):T(R,-1)})}N(T=>Ge(g,1,T),[()=>ut(vt("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",l()?"w-[260px]":"w-[52px]"))]),p(e,g),pa()}Ya(["click"]);var Bf=m('<button class="send-btn active"><!></button>'),Vf=m("<button><!></button>"),Gf=m('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Hf=m('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Uf=m('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Wf=m('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function Dd(e,t){fa(t,!0);let a=St(t,"inputText",15,""),n=St(t,"isLoading",3,!1),l=St(t,"large",3,!1),o=St(t,"placeholder",3,"메시지를 입력하세요..."),s=D(yt([])),d=D(!1),v=D(-1),x=null,g=D(void 0);function k(E){var Y;if(r(d)&&r(s).length>0){if(E.key==="ArrowDown"){E.preventDefault(),c(v,(r(v)+1)%r(s).length);return}if(E.key==="ArrowUp"){E.preventDefault(),c(v,r(v)<=0?r(s).length-1:r(v)-1,!0);return}if(E.key==="Enter"&&r(v)>=0){E.preventDefault(),T(r(s)[r(v)]);return}if(E.key==="Escape"){c(d,!1),c(v,-1);return}}E.key==="Enter"&&!E.shiftKey&&(E.preventDefault(),c(d,!1),(Y=t.onSend)==null||Y.call(t))}function C(E){E.target.style.height="auto",E.target.style.height=Math.min(E.target.scrollHeight,200)+"px"}function R(E){C(E);const Y=a();x&&clearTimeout(x),Y.length>=2&&!/\s/.test(Y.slice(-1))?x=setTimeout(async()=>{var X;try{const Ce=await yd(Y.trim());((X=Ce.results)==null?void 0:X.length)>0?(c(s,Ce.results.slice(0,6),!0),c(d,!0),c(v,-1)):c(d,!1)}catch{c(d,!1)}},300):c(d,!1)}function T(E){a(`${E.corpName} `),c(d,!1),c(v,-1),r(g)&&r(g).focus()}function I(){setTimeout(()=>{c(d,!1)},200)}var y=Wf(),M=i(y),F=i(M);pn(F,E=>c(g,E),()=>r(g));var H=f(F,2);{var _=E=>{var Y=Bf(),X=i(Y);zf(X,{size:14}),$("click",Y,function(...Ce){var lt;(lt=t.onStop)==null||lt.apply(this,Ce)}),p(E,Y)},L=E=>{var Y=Vf(),X=i(Y);{let Ce=se(()=>l()?18:16);uf(X,{get size(){return r(Ce)},strokeWidth:2.5})}N((Ce,lt)=>{Ge(Y,1,Ce),Y.disabled=lt},[()=>ut(vt("send-btn",a().trim()&&"active")),()=>!a().trim()]),$("click",Y,()=>{var Ce;c(d,!1),(Ce=t.onSend)==null||Ce.call(t)}),p(E,Y)};A(H,E=>{n()&&t.onStop?E(_):E(L,-1)})}var U=f(M,2);{var re=E=>{var Y=Uf();we(Y,21,()=>r(s),ye,(X,Ce,lt)=>{var he=Hf(),fe=i(he);Bn(fe,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var W=f(fe,2),Ae=i(W),ot=i(Ae),ge=f(Ae,2),wt=i(ge),ae=f(W,2);{var qt=Ne=>{var h=Gf(),P=i(h);N(()=>S(P,r(Ce).sector)),p(Ne,h)};A(ae,Ne=>{r(Ce).sector&&Ne(qt)})}N(Ne=>{Ge(he,1,Ne),S(ot,r(Ce).corpName),S(wt,`${r(Ce).stockCode??""} · ${(r(Ce).market||"")??""}`)},[()=>ut(vt("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",lt===r(v)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),$("mousedown",he,()=>T(r(Ce))),io("mouseenter",he,()=>{c(v,lt,!0)}),p(X,he)}),p(E,Y)};A(U,E=>{r(d)&&r(s).length>0&&E(re)})}N(E=>{Ge(M,1,E),ka(F,"placeholder",o())},[()=>ut(vt("input-box",l()&&"large"))]),$("keydown",F,k),$("input",F,R),io("blur",F,I),Pn(F,a),p(e,y),pa()}Ya(["keydown","input","click","mousedown"]);var Kf=m('<div class="mb-6 inline-flex items-center gap-2 rounded-full border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-1.5 text-[12px] text-dl-text"><!> <span> </span></div>'),Yf=m('<button class="rounded-2xl border border-dl-border/50 bg-dl-bg-card/40 px-3 py-3 text-left text-[12px] text-dl-text-muted transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:bg-dl-bg-card/65 hover:text-dl-text"> </button>'),Jf=m('<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[720px] flex flex-col items-center"><div class="relative mb-6"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-4">재무 수치와 서술 텍스트를 함께 읽고, 필요하면 원문 근거까지 바로 확인할 수 있습니다</p> <!> <div class="w-full"><!></div> <div class="mt-5 grid w-full gap-3 md:grid-cols-3"><div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Coverage</div> <div class="mt-1 text-[18px] font-semibold text-dl-text">40개 모듈</div> <div class="mt-1 text-[11px] text-dl-text-dim">재무, 주석, 사업, 리스크, 지배구조까지 연결</div></div> <div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Schema</div> <div class="mt-1 text-[18px] font-semibold text-dl-text">표준화 계정</div> <div class="mt-1 text-[11px] text-dl-text-dim">회사마다 다른 XBRL 계정을 비교 가능한 구조로 정리</div></div> <div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3"><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Evidence</div> <div class="mt-1 text-[18px] font-semibold text-dl-text">원문 근거 보존</div> <div class="mt-1 text-[11px] text-dl-text-dim">숫자와 서술 텍스트를 함께 보고 근거까지 바로 열람</div></div></div> <div class="mt-5 grid w-full gap-3 md:grid-cols-3"><button class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"><!> 검색 탐색</button> <button class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"><!> Overview</button> <button class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"><!> 근거 패널</button></div> <div class="surface-panel mt-5 w-full rounded-[24px] border border-dl-border/60 p-4"><div class="mb-3 flex items-center justify-between gap-3"><div><div class="text-[12px] font-medium text-dl-text">바로 시작할 질문</div> <div class="mt-1 text-[11px] text-dl-text-dim">표준화된 계정, 40개 모듈, 원문 근거 보존이라는 DartLab의 강점을 바로 써먹는 질문입니다.</div></div> <span class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] uppercase tracking-[0.16em] text-dl-primary-light">Evidence First</span></div> <div class="grid gap-2 md:grid-cols-3"></div></div></div></div>');function Xf(e,t){fa(t,!0);let a=St(t,"inputText",15,""),n=St(t,"selectedCompany",3,null);const l=["표준화된 계정 기준으로 최근 실적 변화를 비교해줘","사업보고서와 공시 텍스트에서 핵심 리스크를 정리해줘","재무 수치와 원문 근거를 같이 보여주면서 설명해줘"];var o=Jf(),s=i(o),d=f(i(s),6);{var v=_=>{var L=Kf(),U=i(L);Cr(U,{size:13,class:"text-dl-primary-light"});var re=f(U,2),E=i(re);N(()=>S(E,`${(n().corpName||n().company||"선택된 회사")??""} · ${n().stockCode??""}`)),p(_,L)};A(d,_=>{n()&&_(v)})}var x=f(d,2),g=i(x);Dd(g,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get inputText(){return a()},set inputText(_){a(_)}});var k=f(x,4),C=i(k),R=i(C);Bn(R,{size:14});var T=f(C,2),I=i(T);Cr(I,{size:14});var y=f(T,2),M=i(y);Cr(M,{size:14});var F=f(k,2),H=f(i(F),2);we(H,21,()=>l,ye,(_,L)=>{var U=Yf(),re=i(U);N(()=>S(re,r(L))),$("click",U,()=>{a(n()?`${n().corpName||n().company||n().stockCode} ${r(L)}`:r(L))}),p(_,U)}),$("click",C,()=>{var _;return(_=t.onOpenExplorer)==null?void 0:_.call(t,"explore")}),$("click",T,()=>{var _;return(_=t.onOpenExplorer)==null?void 0:_.call(t,"overview")}),$("click",y,()=>{var _;return(_=t.onOpenExplorer)==null?void 0:_.call(t,"evidence")}),p(e,o),pa()}Ya(["click"]);var Qf=m("<span><!></span>");function ms(e,t){fa(t,!0);let a=St(t,"variant",3,"default");const n={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var l=Qf(),o=i(l);di(o,()=>t.children),N(s=>Ge(l,1,s),[()=>ut(vt("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",n[a()],t.class))]),p(e,l),pa()}var Zf=m('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),ep=m('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),tp=m('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),rp=m('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),ap=m('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!></div></div>'),np=m('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),lp=m('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),op=m('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),ip=m('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),sp=m("<button><!> </button>"),dp=m('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),cp=m('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),up=m('<!> <span class="text-dl-text-dim"> </span>',1),vp=m('<div class="flex items-center gap-2 text-[11px]"><!></div>'),fp=m('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),pp=m('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),xp=m('<div class="message-committed"><!></div>'),mp=m('<div><div class="message-live-label"> </div> <pre> </pre></div>'),bp=m('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),gp=m('<span class="text-dl-accent/60"> </span>'),hp=m('<span class="text-dl-success/60"> </span>'),_p=m('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),yp=m('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),wp=m('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),kp=m('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),Cp=m('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),Sp=m("<!>  <div><!> <!></div> <!>",1),Ep=m('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),Mp=m('<span class="text-[10px] text-dl-text-dim"> </span>'),zp=m('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),Tp=m("<button> </button>"),Ap=m('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),Np=m("<button>시스템 프롬프트</button>"),Op=m("<button>LLM 입력</button>"),Ip=m('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),Lp=m('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),Pp=m('<span class="text-dl-text"> </span>'),Rp=m('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),jp=m('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),Dp=m('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),qp=m("<!> <!>",1);function $p(e,t){fa(t,!0);let a=D(null),n=D("context"),l=D("raw"),o=se(()=>{var h,P,B,Q,pe,xe;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((h=t.message.toolEvents)==null?void 0:h.length)>0){const le=[...t.message.toolEvents].reverse().find(Et=>Et.type==="call"),ct=((P=le==null?void 0:le.arguments)==null?void 0:P.module)||((B=le==null?void 0:le.arguments)==null?void 0:B.keyword)||"";return`도구 실행 중 — ${(le==null?void 0:le.name)||""}${ct?` (${ct})`:""}`}if(((Q=t.message.contexts)==null?void 0:Q.length)>0){const le=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(le==null?void 0:le.label)||(le==null?void 0:le.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(pe=t.message.meta)!=null&&pe.company?`${t.message.meta.company} 데이터 검색 중`:(xe=t.message.meta)!=null&&xe.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=se(()=>{var h;return t.message.company||((h=t.message.meta)==null?void 0:h.company)||null}),d=se(()=>{var h,P,B;return t.message.systemPrompt||t.message.userContent||((h=t.message.contexts)==null?void 0:h.length)>0||((P=t.message.meta)==null?void 0:P.includedModules)||((B=t.message.toolEvents)==null?void 0:B.length)>0}),v=se(()=>{var P;const h=(P=t.message.meta)==null?void 0:P.dataYearRange;return h?typeof h=="string"?h:h.min_year&&h.max_year?`${h.min_year}~${h.max_year}년`:null:null});function x(h){if(!h)return 0;const P=(h.match(/[\uac00-\ud7af]/g)||[]).length,B=h.length-P;return Math.round(P*1.5+B/3.5)}function g(h){return h>=1e3?(h/1e3).toFixed(1)+"k":String(h)}let k=se(()=>{var P;let h=0;if(t.message.systemPrompt&&(h+=x(t.message.systemPrompt)),t.message.userContent)h+=x(t.message.userContent);else if(((P=t.message.contexts)==null?void 0:P.length)>0)for(const B of t.message.contexts)h+=x(B.text);return h}),C=se(()=>x(t.message.text));function R(h){const P=h.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(P)||P==="-"||P==="0"}function T(h){if(!h)return"";let P=[],B=[],Q=h.replace(/```(\w*)\n([\s\S]*?)```/g,(xe,le,ct)=>{const Et=P.length;return P.push(ct.trimEnd()),`
%%CODE_${Et}%%
`});Q=Q.replace(/((?:^\|.+\|$\n?)+)/gm,xe=>{const le=xe.trim().split(`
`).filter(Se=>Se.trim());let ct=null,Et=-1,Je=[];for(let Se=0;Se<le.length;Se++)if(le[Se].slice(1,-1).split("|").map(Le=>Le.trim()).every(Le=>/^[\-:]+$/.test(Le))){Et=Se;break}Et>0?(ct=le[Et-1],Je=le.slice(Et+1)):(Et===0||(ct=le[0]),Je=le.slice(1));let ze="<table>";if(ct){const Se=ct.slice(1,-1).split("|").map(Ie=>Ie.trim());ze+="<thead><tr>"+Se.map(Ie=>`<th>${Ie.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(Je.length>0){ze+="<tbody>";for(const Se of Je){const Ie=Se.slice(1,-1).split("|").map(Le=>Le.trim());ze+="<tr>"+Ie.map(Le=>{let zt=Le.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${R(Le)?' class="num"':""}>${zt}</td>`}).join("")+"</tr>"}ze+="</tbody>"}ze+="</table>";let Mt=B.length;return B.push(ze),`
%%TABLE_${Mt}%%
`});let pe=Q.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");pe=pe.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,xe=>"<ul>"+xe.replace(/<br>/g,"")+"</ul>");for(let xe=0;xe<B.length;xe++)pe=pe.replace(`%%TABLE_${xe}%%`,B[xe]);for(let xe=0;xe<P.length;xe++){const le=P[xe].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");pe=pe.replace(`%%CODE_${xe}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${xe}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${le}</code></pre></div>`)}return pe=pe.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(xe,le)=>le.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+pe+"</p>"}let I=D(void 0);const y=/^\s*\|.+\|\s*$/;function M(h,P){if(!h)return{committed:"",draft:"",draftType:"none"};if(!P)return{committed:h,draft:"",draftType:"none"};const B=h.split(`
`);let Q=B.length;h.endsWith(`
`)||(Q=Math.min(Q,B.length-1));let pe=0,xe=-1;for(let ze=0;ze<B.length;ze++)B[ze].trim().startsWith("```")&&(pe+=1,xe=ze);pe%2===1&&xe>=0&&(Q=Math.min(Q,xe));let le=-1;for(let ze=B.length-1;ze>=0;ze--){const Mt=B[ze];if(!Mt.trim())break;if(y.test(Mt))le=ze;else{le=-1;break}}if(le>=0&&(Q=Math.min(Q,le)),Q<=0)return{committed:"",draft:h,draftType:le===0?"table":pe%2===1?"code":"text"};const ct=B.slice(0,Q).join(`
`),Et=B.slice(Q).join(`
`);let Je="text";return Et&&le>=Q?Je="table":Et&&pe%2===1&&(Je="code"),{committed:ct,draft:Et,draftType:Je}}const F='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',H='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function _(h){var pe;const P=h.target.closest(".code-copy-btn");if(!P)return;const B=P.closest(".code-block-wrap"),Q=((pe=B==null?void 0:B.querySelector("code"))==null?void 0:pe.textContent)||"";navigator.clipboard.writeText(Q).then(()=>{P.innerHTML=H,setTimeout(()=>{P.innerHTML=F},2e3)})}function L(h){if(t.onOpenEvidence){t.onOpenEvidence("contexts",h);return}c(a,h,!0),c(n,"context"),c(l,"rendered")}function U(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}c(a,0),c(n,"system"),c(l,"raw")}function re(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}c(a,0),c(n,"snapshot")}function E(h){var P;if(t.onOpenEvidence){const B=(P=t.message.toolEvents)==null?void 0:P[h];t.onOpenEvidence((B==null?void 0:B.type)==="result"?"tool-results":"tool-calls",h);return}c(a,h,!0),c(n,"tool"),c(l,"raw")}function Y(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}c(a,0),c(n,"userContent"),c(l,"raw")}function X(){c(a,null)}function Ce(h){var P,B,Q,pe;return h?h.type==="call"?((P=h.arguments)==null?void 0:P.module)||((B=h.arguments)==null?void 0:B.keyword)||((Q=h.arguments)==null?void 0:Q.engine)||((pe=h.arguments)==null?void 0:pe.name)||"":typeof h.result=="string"?h.result.slice(0,120):h.result&&typeof h.result=="object"&&(h.result.module||h.result.status||h.result.name)||"":""}let lt=se(()=>(t.message.toolEvents||[]).filter(h=>h.type==="call")),he=se(()=>(t.message.toolEvents||[]).filter(h=>h.type==="result")),fe=se(()=>M(t.message.text||"",t.message.loading)),W=se(()=>{var P,B,Q;const h=[];return((B=(P=t.message.meta)==null?void 0:P.includedModules)==null?void 0:B.length)>0&&h.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:Cr}),((Q=t.message.contexts)==null?void 0:Q.length)>0&&h.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:fi}),r(lt).length>0&&h.push({label:`툴 호출 ${r(lt).length}건`,icon:pi}),r(he).length>0&&h.push({label:`툴 결과 ${r(he).length}건`,icon:Rn}),t.message.systemPrompt&&h.push({label:"시스템 프롬프트",icon:no}),t.message.userContent&&h.push({label:"LLM 입력",icon:zn}),h}),Ae=se(()=>{var P,B,Q;if(!t.message.loading)return[];const h=[];return(P=t.message.meta)!=null&&P.company&&h.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&h.push({label:"핵심 수치 확인",done:!0}),(B=t.message.meta)!=null&&B.includedModules&&h.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((Q=t.message.contexts)==null?void 0:Q.length)>0&&h.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&h.push({label:"프롬프트 조립",done:!0}),t.message.text?h.push({label:"응답 작성 중",done:!1}):h.push({label:r(o)||"준비 중",done:!1}),h});var ot=qp(),ge=te(ot);{var wt=h=>{var P=Zf(),B=f(i(P),2),Q=i(B),pe=i(Q);N(()=>S(pe,t.message.text)),p(h,P)},ae=h=>{var P=Ep(),B=f(i(P),2),Q=i(B);{var pe=Se=>{var Ie=ap(),Le=i(Ie),zt=i(Le);cf(zt,{size:11});var Ot=f(Le,4),mt=i(Ot);{var Fe=ie=>{ms(ie,{variant:"muted",children:(ne,be)=>{var Ee=sa();N(()=>S(Ee,r(s))),p(ne,Ee)},$$slots:{default:!0}})};A(mt,ie=>{r(s)&&ie(Fe)})}var bt=f(mt,2);{var Tt=ie=>{ms(ie,{variant:"accent",children:(ne,be)=>{var Ee=sa();N(()=>S(Ee,r(v))),p(ne,Ee)},$$slots:{default:!0}})};A(bt,ie=>{r(v)&&ie(Tt)})}var $e=f(bt,2);{var Be=ie=>{var ne=Me(),be=te(ne);we(be,17,()=>t.message.contexts,ye,(Ee,Xe,Qe)=>{var gt=ep(),$t=i(gt);Cr($t,{size:10,class:"flex-shrink-0"});var Vt=f($t);N(()=>S(Vt,` ${(r(Xe).label||r(Xe).module)??""}`)),$("click",gt,()=>L(Qe)),p(Ee,gt)}),p(ie,ne)},Te=ie=>{var ne=tp(),be=i(ne);Cr(be,{size:10,class:"flex-shrink-0"});var Ee=f(be);N(()=>S(Ee,` 모듈 ${t.message.meta.includedModules.length??""}개`)),p(ie,ne)};A($e,ie=>{var ne,be,Ee;((ne=t.message.contexts)==null?void 0:ne.length)>0?ie(Be):((Ee=(be=t.message.meta)==null?void 0:be.includedModules)==null?void 0:Ee.length)>0&&ie(Te,1)})}var rt=f($e,2);we(rt,17,()=>r(W),ye,(ie,ne)=>{var be=rp(),Ee=i(be);zu(Ee,()=>r(ne).icon,(Qe,gt)=>{gt(Qe,{size:10,class:"flex-shrink-0"})});var Xe=f(Ee);N(()=>S(Xe,` ${r(ne).label??""}`)),$("click",be,()=>{r(ne).label.startsWith("컨텍스트")?L(0):r(ne).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):E(0):r(ne).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):E((t.message.toolEvents||[]).findIndex(Qe=>Qe.type==="result")):r(ne).label==="시스템 프롬프트"?U():r(ne).label==="LLM 입력"&&Y()}),p(ie,be)}),p(Se,Ie)};A(Q,Se=>{var Ie,Le;(r(s)||r(v)||((Ie=t.message.contexts)==null?void 0:Ie.length)>0||(Le=t.message.meta)!=null&&Le.includedModules||r(W).length>0)&&Se(pe)})}var xe=f(Q,2);{var le=Se=>{var Ie=ip(),Le=i(Ie);we(Le,21,()=>t.message.snapshot.items,ye,(mt,Fe)=>{const bt=se(()=>r(Fe).status==="good"?"text-dl-success":r(Fe).status==="danger"?"text-dl-primary-light":r(Fe).status==="caution"?"text-amber-400":"text-dl-text");var Tt=np(),$e=i(Tt),Be=i($e),Te=f($e,2),rt=i(Te);N(ie=>{S(Be,r(Fe).label),Ge(Te,1,ie),S(rt,r(Fe).value)},[()=>ut(vt("text-[14px] font-semibold leading-snug mt-0.5",r(bt)))]),p(mt,Tt)});var zt=f(Le,2);{var Ot=mt=>{var Fe=op();we(Fe,21,()=>t.message.snapshot.warnings,ye,(bt,Tt)=>{var $e=lp(),Be=i($e);Nf(Be,{size:10});var Te=f(Be);N(()=>S(Te,` ${r(Tt)??""}`)),p(bt,$e)}),p(mt,Fe)};A(zt,mt=>{var Fe;((Fe=t.message.snapshot.warnings)==null?void 0:Fe.length)>0&&mt(Ot)})}$("click",Ie,re),p(Se,Ie)};A(xe,Se=>{var Ie,Le;((Le=(Ie=t.message.snapshot)==null?void 0:Ie.items)==null?void 0:Le.length)>0&&Se(le)})}var ct=f(xe,2);{var Et=Se=>{var Ie=dp(),Le=i(Ie),zt=f(i(Le),4);we(zt,21,()=>t.message.toolEvents,ye,(Ot,mt,Fe)=>{const bt=se(()=>Ce(r(mt)));var Tt=sp(),$e=i(Tt);{var Be=ie=>{pi(ie,{size:11})},Te=ie=>{Rn(ie,{size:11})};A($e,ie=>{r(mt).type==="call"?ie(Be):ie(Te,-1)})}var rt=f($e);N(ie=>{Ge(Tt,1,ie),S(rt,` ${(r(mt).type==="call"?r(mt).name:`${r(mt).name} 결과`)??""}${r(bt)?`: ${r(bt)}`:""}`)},[()=>ut(vt("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",r(mt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),$("click",Tt,()=>E(Fe)),p(Ot,Tt)}),p(Se,Ie)};A(ct,Se=>{var Ie;((Ie=t.message.toolEvents)==null?void 0:Ie.length)>0&&Se(Et)})}var Je=f(ct,2);{var ze=Se=>{var Ie=fp(),Le=i(Ie);we(Le,21,()=>r(Ae),ye,(zt,Ot)=>{var mt=vp(),Fe=i(mt);{var bt=$e=>{var Be=cp(),Te=f(te(Be),2),rt=i(Te);N(()=>S(rt,r(Ot).label)),p($e,Be)},Tt=$e=>{var Be=up(),Te=te(Be);Tr(Te,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var rt=f(Te,2),ie=i(rt);N(()=>S(ie,r(Ot).label)),p($e,Be)};A(Fe,$e=>{r(Ot).done?$e(bt):$e(Tt,-1)})}p(zt,mt)}),p(Se,Ie)},Mt=Se=>{var Ie=Sp(),Le=te(Ie);{var zt=Te=>{var rt=pp(),ie=i(rt);Tr(ie,{size:12,class:"animate-spin flex-shrink-0"});var ne=f(ie,2),be=i(ne);N(()=>S(be,r(o))),p(Te,rt)};A(Le,Te=>{t.message.loading&&Te(zt)})}var Ot=f(Le,2),mt=i(Ot);{var Fe=Te=>{var rt=xp(),ie=i(rt);Wi(ie,()=>T(r(fe).committed)),p(Te,rt)};A(mt,Te=>{r(fe).committed&&Te(Fe)})}var bt=f(mt,2);{var Tt=Te=>{var rt=mp(),ie=i(rt),ne=i(ie),be=f(ie,2),Ee=i(be);N(Xe=>{Ge(rt,1,Xe),S(ne,r(fe).draftType==="table"?"표 구성 중":r(fe).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),S(Ee,r(fe).draft)},[()=>ut(vt("message-live-tail",r(fe).draftType==="table"&&"message-draft-table",r(fe).draftType==="code"&&"message-draft-code"))]),p(Te,rt)};A(bt,Te=>{r(fe).draft&&Te(Tt)})}pn(Ot,Te=>c(I,Te),()=>r(I));var $e=f(Ot,2);{var Be=Te=>{var rt=Cp(),ie=i(rt);{var ne=ht=>{var Pe=bp(),Ft=i(Pe);ff(Ft,{size:10});var Z=f(Ft);N(()=>S(Z,` ${t.message.duration??""}초`)),p(ht,Pe)};A(ie,ht=>{t.message.duration&&ht(ne)})}var be=f(ie,2);{var Ee=ht=>{var Pe=_p(),Ft=i(Pe);{var Z=kt=>{var Bt=gp(),_r=i(Bt);N(vr=>S(_r,`↑${vr??""}`),[()=>g(r(k))]),p(kt,Bt)};A(Ft,kt=>{r(k)>0&&kt(Z)})}var Ue=f(Ft,2);{var Pt=kt=>{var Bt=hp(),_r=i(Bt);N(vr=>S(_r,`↓${vr??""}`),[()=>g(r(C))]),p(kt,Bt)};A(Ue,kt=>{r(C)>0&&kt(Pt)})}p(ht,Pe)};A(be,ht=>{(r(k)>0||r(C)>0)&&ht(Ee)})}var Xe=f(be,2);{var Qe=ht=>{var Pe=yp(),Ft=i(Pe);kf(Ft,{size:10}),$("click",Pe,()=>{var Z;return(Z=t.onRegenerate)==null?void 0:Z.call(t)}),p(ht,Pe)};A(Xe,ht=>{t.onRegenerate&&ht(Qe)})}var gt=f(Xe,2);{var $t=ht=>{var Pe=wp(),Ft=i(Pe);no(Ft,{size:10}),$("click",Pe,U),p(ht,Pe)};A(gt,ht=>{t.message.systemPrompt&&ht($t)})}var Vt=f(gt,2);{var ir=ht=>{var Pe=kp(),Ft=i(Pe);zn(Ft,{size:10});var Z=f(Ft);N((Ue,Pt)=>S(Z,` LLM 입력 (${Ue??""}자 · ~${Pt??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>g(x(t.message.userContent))]),$("click",Pe,Y),p(ht,Pe)};A(Vt,ht=>{t.message.userContent&&ht(ir)})}p(Te,rt)};A($e,Te=>{!t.message.loading&&(t.message.duration||r(d)||t.onRegenerate)&&Te(Be)})}N(Te=>Ge(Ot,1,Te),[()=>ut(vt("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),$("click",Ot,_),p(Se,Ie)};A(Je,Se=>{t.message.loading&&!t.message.text?Se(ze):Se(Mt,-1)})}p(h,P)};A(ge,h=>{t.message.role==="user"?h(wt):h(ae,-1)})}var qt=f(ge,2);{var Ne=h=>{const P=se(()=>r(n)==="system"),B=se(()=>r(n)==="userContent"),Q=se(()=>r(n)==="context"),pe=se(()=>r(n)==="snapshot"),xe=se(()=>r(n)==="tool"),le=se(()=>{var Z;return r(Q)?(Z=t.message.contexts)==null?void 0:Z[r(a)]:null}),ct=se(()=>{var Z;return r(xe)?(Z=t.message.toolEvents)==null?void 0:Z[r(a)]:null}),Et=se(()=>{var Z,Ue,Pt,kt,Bt;return r(pe)?"핵심 수치 (원본 데이터)":r(P)?"시스템 프롬프트":r(B)?"LLM에 전달된 입력":r(xe)?((Z=r(ct))==null?void 0:Z.type)==="call"?`${(Ue=r(ct))==null?void 0:Ue.name} 호출`:`${(Pt=r(ct))==null?void 0:Pt.name} 결과`:((kt=r(le))==null?void 0:kt.label)||((Bt=r(le))==null?void 0:Bt.module)||""}),Je=se(()=>{var Z;return r(pe)?JSON.stringify(t.message.snapshot,null,2):r(P)?t.message.systemPrompt:r(B)?t.message.userContent:r(xe)?JSON.stringify(r(ct),null,2):(Z=r(le))==null?void 0:Z.text});var ze=Dp(),Mt=i(ze),Se=i(Mt),Ie=i(Se),Le=i(Ie),zt=i(Le);{var Ot=Z=>{Cr(Z,{size:15,class:"text-dl-success flex-shrink-0"})},mt=Z=>{no(Z,{size:15,class:"text-dl-primary-light flex-shrink-0"})},Fe=Z=>{zn(Z,{size:15,class:"text-dl-accent flex-shrink-0"})},bt=Z=>{Cr(Z,{size:15,class:"flex-shrink-0"})};A(zt,Z=>{r(pe)?Z(Ot):r(P)?Z(mt,1):r(B)?Z(Fe,2):Z(bt,-1)})}var Tt=f(zt,2),$e=i(Tt),Be=f(Tt,2);{var Te=Z=>{var Ue=Mp(),Pt=i(Ue);N(kt=>S(Pt,`(${kt??""}자)`),[()=>{var kt,Bt;return(Bt=(kt=r(Je))==null?void 0:kt.length)==null?void 0:Bt.toLocaleString()}]),p(Z,Ue)};A(Be,Z=>{r(P)&&Z(Te)})}var rt=f(Le,2),ie=i(rt);{var ne=Z=>{var Ue=zp(),Pt=i(Ue),kt=i(Pt);zn(kt,{size:11});var Bt=f(Pt,2),_r=i(Bt);pf(_r,{size:11}),N((vr,Nr)=>{Ge(Pt,1,vr),Ge(Bt,1,Nr)},[()=>ut(vt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(l)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>ut(vt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(l)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),$("click",Pt,()=>c(l,"rendered")),$("click",Bt,()=>c(l,"raw")),p(Z,Ue)};A(ie,Z=>{r(Q)&&Z(ne)})}var be=f(ie,2),Ee=i(be);Xn(Ee,{size:18});var Xe=f(Ie,2);{var Qe=Z=>{var Ue=Ap(),Pt=i(Ue);we(Pt,21,()=>t.message.contexts,ye,(kt,Bt,_r)=>{var vr=Tp(),Nr=i(vr);N(Vr=>{Ge(vr,1,Vr),S(Nr,t.message.contexts[_r].label||t.message.contexts[_r].module)},[()=>ut(vt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",_r===r(a)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),$("click",vr,()=>{c(a,_r,!0)}),p(kt,vr)}),p(Z,Ue)};A(Xe,Z=>{var Ue;r(Q)&&((Ue=t.message.contexts)==null?void 0:Ue.length)>1&&Z(Qe)})}var gt=f(Xe,2);{var $t=Z=>{var Ue=Ip(),Pt=i(Ue),kt=i(Pt);{var Bt=Nr=>{var Vr=Np();N(qa=>Ge(Vr,1,qa),[()=>ut(vt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(P)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),$("click",Vr,()=>{c(n,"system")}),p(Nr,Vr)};A(kt,Nr=>{t.message.systemPrompt&&Nr(Bt)})}var _r=f(kt,2);{var vr=Nr=>{var Vr=Op();N(qa=>Ge(Vr,1,qa),[()=>ut(vt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(B)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),$("click",Vr,()=>{c(n,"userContent")}),p(Nr,Vr)};A(_r,Nr=>{t.message.userContent&&Nr(vr)})}p(Z,Ue)};A(gt,Z=>{!r(Q)&&!r(pe)&&!r(xe)&&Z($t)})}var Vt=f(Se,2),ir=i(Vt);{var ht=Z=>{var Ue=Lp(),Pt=i(Ue);Wi(Pt,()=>{var kt;return T((kt=r(le))==null?void 0:kt.text)}),p(Z,Ue)},Pe=Z=>{var Ue=Rp(),Pt=i(Ue),kt=f(i(Pt),2),Bt=i(kt),_r=f(Bt);{var vr=Ma=>{var xa=Pp(),hn=i(xa);N(Hn=>S(hn,Hn),[()=>Ce(r(ct))]),p(Ma,xa)},Nr=se(()=>Ce(r(ct)));A(_r,Ma=>{r(Nr)&&Ma(vr)})}var Vr=f(Pt,2),qa=i(Vr);N(()=>{var Ma;S(Bt,`${((Ma=r(ct))==null?void 0:Ma.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),S(qa,r(Je))}),p(Z,Ue)},Ft=Z=>{var Ue=jp(),Pt=i(Ue);N(()=>S(Pt,r(Je))),p(Z,Ue)};A(ir,Z=>{r(Q)&&r(l)==="rendered"?Z(ht):r(xe)?Z(Pe,1):Z(Ft,-1)})}N(()=>S($e,r(Et))),$("click",ze,Z=>{Z.target===Z.currentTarget&&X()}),$("keydown",ze,Z=>{Z.key==="Escape"&&X()}),$("click",be,X),p(h,ze)};A(qt,h=>{r(a)!==null&&h(Ne)})}p(e,ot),pa()}Ya(["click","keydown"]);var Fp=m('<div class="surface-panel flex flex-wrap items-center gap-2 rounded-2xl border border-dl-primary/20 bg-dl-primary/[0.05] px-4 py-3"><div class="flex items-center gap-2 text-[12px] text-dl-text"><!> <span class="font-medium"> </span> <span class="text-dl-text-dim"> </span></div> <div class="flex flex-wrap gap-1.5 ml-auto"><button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> Overview</button> <button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> Explore</button> <button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> Evidence</button></div></div>'),Bp=m('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Vp=m('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Gp=m('<div class="flex justify-end gap-2 mb-1.5"><button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 탐색</button> <button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 근거</button> <!></div>'),Hp=m('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-14 pb-10 space-y-8"><!> <!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Up(e,t){fa(t,!0);function a(he){if(l())return!1;for(let fe=n().length-1;fe>=0;fe--)if(n()[fe].role==="assistant"&&!n()[fe].error&&n()[fe].text)return fe===he;return!1}let n=St(t,"messages",19,()=>[]),l=St(t,"isLoading",3,!1),o=St(t,"inputText",15,""),s=St(t,"scrollTrigger",3,0),d=St(t,"selectedCompany",3,null),v,x,g=D(!0),k=D(!1),C=D(!0);function R(){if(!v)return;const{scrollTop:he,scrollHeight:fe,clientHeight:W}=v;c(C,fe-he-W<96),r(C)?(c(g,!0),c(k,!1)):(c(g,!1),c(k,!0))}function T(he="smooth"){x&&(x.scrollIntoView({block:"end",behavior:he}),c(g,!0),c(k,!1))}na(()=>{s(),!(!v||!x)&&requestAnimationFrame(()=>{!v||!x||(r(g)||r(C)?(x.scrollIntoView({block:"end",behavior:l()?"auto":"smooth"}),c(k,!1)):c(k,!0))})});var I=Hp(),y=i(I),M=i(y),F=i(M);{var H=he=>{var fe=Fp(),W=i(fe),Ae=i(W);Cr(Ae,{size:13,class:"text-dl-primary-light"});var ot=f(Ae,2),ge=i(ot),wt=f(ot,2),ae=i(wt),qt=f(W,2),Ne=i(qt),h=i(Ne);Cr(h,{size:10,class:"inline mr-1"});var P=f(Ne,2),B=i(P);Bn(B,{size:10,class:"inline mr-1"});var Q=f(P,2),pe=i(Q);Cr(pe,{size:10,class:"inline mr-1"}),N(()=>{S(ge,d().corpName||d().company||"선택된 회사"),S(ae,d().stockCode)}),$("click",Ne,()=>{var xe;return(xe=t.onOpenExplorer)==null?void 0:xe.call(t,"overview")}),$("click",P,()=>{var xe;return(xe=t.onOpenExplorer)==null?void 0:xe.call(t,"explore")}),$("click",Q,()=>{var xe;return(xe=t.onOpenExplorer)==null?void 0:xe.call(t,"evidence")}),p(he,fe)};A(F,he=>{d()&&he(H)})}var _=f(F,2);we(_,17,n,ye,(he,fe,W)=>{{let Ae=se(()=>a(W)?t.onRegenerate:void 0);$p(he,{get message(){return r(fe)},get onRegenerate(){return r(Ae)},get onOpenEvidence(){return t.onOpenEvidence}})}});var L=f(_,2);pn(L,he=>x=he,()=>x),pn(y,he=>v=he,()=>v);var U=f(y,2);{var re=he=>{var fe=Bp(),W=i(fe);$("click",W,()=>T("smooth")),p(he,fe)};A(U,he=>{r(k)&&he(re)})}var E=f(U,2),Y=i(E),X=i(Y);{var Ce=he=>{var fe=Gp(),W=i(fe),Ae=i(W);Bn(Ae,{size:10});var ot=f(W,2),ge=i(ot);Cr(ge,{size:10});var wt=f(ot,2);{var ae=qt=>{var Ne=Vp(),h=i(Ne);jn(h,{size:10}),$("click",Ne,function(...P){var B;(B=t.onExport)==null||B.apply(this,P)}),p(qt,Ne)};A(wt,qt=>{n().length>1&&t.onExport&&qt(ae)})}$("click",W,()=>{var qt;return(qt=t.onOpenExplorer)==null?void 0:qt.call(t,"explore")}),$("click",ot,()=>{var qt;return(qt=t.onOpenExplorer)==null?void 0:qt.call(t,"evidence")}),p(he,fe)};A(X,he=>{l()||he(Ce)})}var lt=f(X,2);Dd(lt,{get isLoading(){return l()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get inputText(){return o()},set inputText(he){o(he)}}),io("scroll",y,R),p(e,I),pa()}Ya(["click"]);var Wp=m('<span class="period-badge svelte-1l2nqwu"> </span>'),Kp=m('<div class="view-modes svelte-1l2nqwu"><button>본문</button> <button>변화 비교</button></div>'),Yp=m('<div class="loading svelte-1l2nqwu"><!> 공시 데이터 로딩 중...</div>'),Jp=m('<span class="change-badge svelte-1l2nqwu"> </span>'),Xp=m('<button><span class="toc-icon svelte-1l2nqwu"> </span> <span class="toc-label svelte-1l2nqwu"> </span> <!></button>'),Qp=m('<div class="toc-chapter"><button class="toc-chapter-btn svelte-1l2nqwu"><!> <span> </span></button> <!></div>'),Zp=m('<div class="empty svelte-1l2nqwu"><!> <p>좌측에서 섹션을 선택하세요</p></div>'),ex=m('<div class="loading svelte-1l2nqwu"><!></div>'),tx=m('<button><span class="block-num svelte-1l2nqwu"> </span> <span> </span> <span class="block-source svelte-1l2nqwu"> </span> <span class="block-preview svelte-1l2nqwu"> </span></button>'),rx=m('<div class="block-list svelte-1l2nqwu"></div>'),ax=m('<th class="svelte-1l2nqwu"> </th>'),nx=m('<td class="svelte-1l2nqwu"> </td>'),lx=m('<tr class="svelte-1l2nqwu"></tr>'),ox=m('<div class="table-wrapper svelte-1l2nqwu"><table class="data-table svelte-1l2nqwu"><thead><tr></tr></thead><tbody></tbody></table></div>'),ix=m('<div class="text-content svelte-1l2nqwu"> </div>'),sx=m('<th class="svelte-1l2nqwu"> </th>'),dx=m('<td class="svelte-1l2nqwu"> </td>'),cx=m('<tr class="svelte-1l2nqwu"></tr>'),ux=m('<div class="table-wrapper svelte-1l2nqwu"><table class="data-table svelte-1l2nqwu"><thead><tr></tr></thead><tbody></tbody></table></div>'),vx=m('<div class="empty svelte-1l2nqwu">데이터 없음</div>'),fx=m('<div class="block-content svelte-1l2nqwu"><!></div>'),px=m('<div class="topic-header svelte-1l2nqwu"><h3 class="svelte-1l2nqwu"> </h3></div> <!> <!>',1),xx=m("<option> </option>"),mx=m("<option> </option>"),bx=m('<div><span class="diff-marker svelte-1l2nqwu"> </span> <span class="diff-text svelte-1l2nqwu"> </span></div>'),gx=m('<div class="diff-view svelte-1l2nqwu"></div>'),hx=m('<div class="empty svelte-1l2nqwu">이 기간에는 변화가 없습니다</div>'),_x=m('<div class="empty svelte-1l2nqwu">기간을 선택하고 비교를 누르세요</div>'),yx=m('<div class="topic-header svelte-1l2nqwu"><h3 class="svelte-1l2nqwu"> </h3></div> <div class="diff-controls svelte-1l2nqwu"><select class="svelte-1l2nqwu"><option>이전 기간</option><!></select> <span class="diff-arrow svelte-1l2nqwu">→</span> <select class="svelte-1l2nqwu"><option>이후 기간</option><!></select> <button class="diff-run-btn svelte-1l2nqwu">비교</button></div> <!>',1),wx=m('<div class="viewer-body svelte-1l2nqwu"><nav class="toc svelte-1l2nqwu"></nav> <main class="content svelte-1l2nqwu"><!></main></div>'),kx=m('<div class="viewer svelte-1l2nqwu"><div class="viewer-header svelte-1l2nqwu"><div class="header-left svelte-1l2nqwu"><h2 class="svelte-1l2nqwu"> </h2> <!></div> <!></div> <!></div>');function Cx(e,t){fa(t,!0);let a=St(t,"stockCode",3,null),n=St(t,"corpName",3,""),l=D(null),o=D(null),s=D(!1),d=D(yt(new Set)),v=D(null),x=D(null),g=D(null),k=D(null),C=D(!1),R=D(""),T=D(""),I=D(null),y=D("content"),M=D(yt([]));na(()=>{a()&&F()});async function F(){var h;c(s,!0);try{const[P,B]=await Promise.all([Zu(a()),ev(a())]);c(l,P.payload,!0),c(o,B.payload,!0),(h=r(l))!=null&&h.columns&&c(M,r(l).columns.filter(Q=>/^\d{4}(Q[1-4])?$/.test(Q)),!0)}catch(P){console.error("viewer load error:",P)}c(s,!1)}async function H(h){c(v,h,!0),c(x,null),c(g,null),c(k,null),c(I,null),c(y,"content"),c(C,!0);try{const P=await es(a(),h);c(x,P.payload,!0)}catch(P){console.error("block index error:",P)}c(C,!1)}async function _(h){c(k,h,!0),c(g,null),c(C,!0);try{const P=await es(a(),r(v),h);c(g,P.payload,!0)}catch(P){console.error("block data error:",P)}c(C,!1)}async function L(){if(!(!r(R)||!r(T)||!r(v))){c(I,null),c(C,!0);try{const h=await tv(a(),r(v),r(R),r(T));c(I,h.payload,!0)}catch(h){console.error("diff load error:",h)}c(C,!1)}}function U(h){const P=new Set(r(d));P.has(h)?P.delete(h):P.add(h),c(d,P,!0)}function re(h){if(!h)return[];const P=[];let B=null;const Q=new Set;for(const pe of h){const xe=pe.chapter||"";(!B||B.chapter!==xe)&&(B={chapter:xe,topics:[]},P.push(B));const le=pe.topic;if(!Q.has(le)){Q.add(le);const ct=pe.source||"docs";B.topics.push({topic:le,source:ct})}}return P}function E(h){var P;return(P=r(o))!=null&&P.rows?r(o).rows.find(B=>B.topic===h):null}function Y(h){return h==="finance"?"📊":h==="report"?"📋":""}function X(h){return h==="text"?"텍스트":h==="table"?"테이블":h}var Ce=kx(),lt=i(Ce),he=i(lt),fe=i(he),W=i(fe),Ae=f(fe,2);{var ot=h=>{var P=Wp(),B=i(P);N(()=>S(B,`${r(M)[0]??""} ~ ${r(M)[r(M).length-1]??""}`)),p(h,P)};A(Ae,h=>{r(M).length&&h(ot)})}var ge=f(he,2);{var wt=h=>{var P=Kp(),B=i(P);let Q;var pe=f(B,2);let xe;N(()=>{Q=Ge(B,1,"svelte-1l2nqwu",null,Q,{active:r(y)==="content"}),xe=Ge(pe,1,"svelte-1l2nqwu",null,xe,{active:r(y)==="diff"})}),$("click",B,()=>c(y,"content")),$("click",pe,()=>c(y,"diff")),p(h,P)};A(ge,h=>{r(v)&&h(wt)})}var ae=f(lt,2);{var qt=h=>{var P=Yp(),B=i(P);Tr(B,{class:"spin",size:20}),p(h,P)},Ne=h=>{var P=wx(),B=i(P);we(B,21,()=>re(r(l).rows),ye,(Je,ze)=>{var Mt=Qp(),Se=i(Mt),Ie=i(Se);{var Le=Be=>{jd(Be,{size:14})},zt=se(()=>r(d).has(r(ze).chapter)),Ot=Be=>{vi(Be,{size:14})};A(Ie,Be=>{r(zt)?Be(Le):Be(Ot,-1)})}var mt=f(Ie,2),Fe=i(mt),bt=f(Se,2);{var Tt=Be=>{var Te=Me(),rt=te(Te);we(rt,17,()=>r(ze).topics,ye,(ie,ne)=>{const be=se(()=>E(r(ne).topic));var Ee=Xp();let Xe;var Qe=i(Ee),gt=i(Qe),$t=f(Qe,2),Vt=i($t),ir=f($t,2);{var ht=Pe=>{var Ft=Jp(),Z=i(Ft);N(()=>S(Z,r(be).changed)),p(Pe,Ft)};A(ir,Pe=>{var Ft;(Ft=r(be))!=null&&Ft.changed&&r(be).changed>0&&Pe(ht)})}N(Pe=>{Xe=Ge(Ee,1,"toc-topic svelte-1l2nqwu",null,Xe,{active:r(v)===r(ne).topic}),S(gt,Pe),S(Vt,r(ne).topic)},[()=>Y(r(ne).source)]),$("click",Ee,()=>H(r(ne).topic)),p(ie,Ee)}),p(Be,Te)},$e=se(()=>r(d).has(r(ze).chapter));A(bt,Be=>{r($e)&&Be(Tt)})}N(()=>S(Fe,r(ze).chapter||"기타")),$("click",Se,()=>U(r(ze).chapter)),p(Je,Mt)});var Q=f(B,2),pe=i(Q);{var xe=Je=>{var ze=Zp(),Mt=i(ze);zn(Mt,{size:32,strokeWidth:1}),p(Je,ze)},le=Je=>{var ze=ex(),Mt=i(ze);Tr(Mt,{class:"spin",size:20}),p(Je,ze)},ct=Je=>{var ze=px(),Mt=te(ze),Se=i(Mt),Ie=i(Se),Le=f(Mt,2);{var zt=Fe=>{var bt=rx();we(bt,21,()=>r(x).rows,ye,(Tt,$e)=>{var Be=tx();let Te;var rt=i(Be),ie=i(rt),ne=f(rt,2);let be;var Ee=i(ne),Xe=f(ne,2),Qe=i(Xe),gt=f(Xe,2),$t=i(gt);N((Vt,ir)=>{Te=Ge(Be,1,"block-item svelte-1l2nqwu",null,Te,{active:r(k)===r($e).block}),S(ie,r($e).block),be=Ge(ne,1,"block-type svelte-1l2nqwu",null,be,{text:r($e).type==="text",table:r($e).type==="table"}),S(Ee,Vt),S(Qe,ir),S($t,r($e).preview||"")},[()=>X(r($e).type),()=>Y(r($e).source)]),$("click",Be,()=>_(r($e).block)),p(Tt,Be)}),p(Fe,bt)};A(Le,Fe=>{var bt;(bt=r(x))!=null&&bt.rows&&Fe(zt)})}var Ot=f(Le,2);{var mt=Fe=>{var bt=fx(),Tt=i(bt);{var $e=ie=>{var ne=ox(),be=i(ne),Ee=i(be),Xe=i(Ee);we(Xe,21,()=>r(g).columns,ye,(gt,$t)=>{var Vt=ax(),ir=i(Vt);N(()=>S(ir,r($t))),p(gt,Vt)});var Qe=f(Ee);we(Qe,21,()=>r(g).rows,ye,(gt,$t)=>{var Vt=lx();we(Vt,21,()=>r(g).columns,ye,(ir,ht)=>{var Pe=nx(),Ft=i(Pe);N(()=>S(Ft,r($t)[r(ht)]??"")),p(ir,Pe)}),p(gt,Vt)}),p(ie,ne)},Be=ie=>{var ne=ix(),be=i(ne);N(()=>S(be,r(g).data)),p(ie,ne)},Te=ie=>{var ne=ux(),be=i(ne),Ee=i(be),Xe=i(Ee);we(Xe,21,()=>r(g).columns,ye,(gt,$t)=>{var Vt=sx(),ir=i(Vt);N(()=>S(ir,r($t))),p(gt,Vt)});var Qe=f(Ee);we(Qe,21,()=>r(g).rows,ye,(gt,$t)=>{var Vt=cx();we(Vt,21,()=>r(g).columns,ye,(ir,ht)=>{var Pe=dx(),Ft=i(Pe);N(()=>S(Ft,r($t)[r(ht)]??"")),p(ir,Pe)}),p(gt,Vt)}),p(ie,ne)},rt=ie=>{var ne=vx();p(ie,ne)};A(Tt,ie=>{r(g).type==="table"&&r(g).rows?ie($e):r(g).type==="text"&&r(g).data?ie(Be,1):r(g).rows?ie(Te,2):ie(rt,-1)})}p(Fe,bt)};A(Ot,Fe=>{r(g)&&Fe(mt)})}N(()=>S(Ie,r(v))),p(Je,ze)},Et=Je=>{var ze=yx(),Mt=te(ze),Se=i(Mt),Ie=i(Se),Le=f(Mt,2),zt=i(Le),Ot=i(zt);Ot.value=Ot.__value="";var mt=f(Ot);we(mt,17,()=>r(M),ye,(ne,be)=>{var Ee=xx(),Xe=i(Ee),Qe={};N(()=>{S(Xe,r(be)),Qe!==(Qe=r(be))&&(Ee.value=(Ee.__value=r(be))??"")}),p(ne,Ee)});var Fe=f(zt,4),bt=i(Fe);bt.value=bt.__value="";var Tt=f(bt);we(Tt,17,()=>r(M),ye,(ne,be)=>{var Ee=mx(),Xe=i(Ee),Qe={};N(()=>{S(Xe,r(be)),Qe!==(Qe=r(be))&&(Ee.value=(Ee.__value=r(be))??"")}),p(ne,Ee)});var $e=f(Fe,2),Be=f(Le,2);{var Te=ne=>{var be=gx();we(be,21,()=>r(I).rows,ye,(Ee,Xe)=>{var Qe=bx();let gt;var $t=i(Qe),Vt=i($t),ir=f($t,2),ht=i(ir);N(()=>{gt=Ge(Qe,1,"diff-line svelte-1l2nqwu",null,gt,{added:r(Xe).status==="+",removed:r(Xe).status==="-"}),S(Vt,r(Xe).status||" "),S(ht,r(Xe).text)}),p(Ee,Qe)}),p(ne,be)},rt=ne=>{var be=hx();p(ne,be)},ie=ne=>{var be=_x();p(ne,be)};A(Be,ne=>{var be;((be=r(I))==null?void 0:be.type)==="table"&&r(I).rows?ne(Te):r(I)?ne(rt,1):ne(ie,-1)})}N(()=>S(Ie,`${r(v)??""} — 변화 비교`)),Ji(zt,()=>r(R),ne=>c(R,ne)),Ji(Fe,()=>r(T),ne=>c(T,ne)),$("click",$e,L),p(Je,ze)};A(pe,Je=>{r(v)?r(C)?Je(le,1):r(y)==="content"?Je(ct,2):r(y)==="diff"&&Je(Et,3):Je(xe)})}p(h,P)};A(ae,h=>{var P;r(s)?h(qt):(P=r(l))!=null&&P.rows&&h(Ne,1)})}N(()=>S(W,n()||a())),p(e,Ce),pa()}Ya(["click"]);var Sx=m('<button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="워크스페이스 닫기"><!></button>'),Ex=m('<button class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-white/[0.04]"><div class="flex h-8 w-8 items-center justify-center rounded-lg bg-dl-primary/10 text-[11px] font-semibold text-dl-primary-light"> </div> <div class="min-w-0 flex-1"><div class="truncate text-[12px] font-medium text-dl-text"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></button>'),Mx=m('<div class="mt-2 space-y-1 rounded-xl border border-dl-border/50 bg-dl-bg-darker/95 p-1"></div>'),zx=m('<div class="mt-3 rounded-2xl border border-dl-primary/20 bg-dl-primary/[0.05] p-3"><div class="flex items-start justify-between gap-3"><div class="min-w-0"><div class="text-[13px] font-semibold text-dl-text"> </div> <div class="mt-0.5 text-[10px] text-dl-text-dim"> <!> <!></div></div> <button class="rounded-lg px-2 py-1 text-[10px] text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text">초기화</button></div> <div class="mt-2 flex gap-2"><button class="rounded-lg border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button> <button class="rounded-lg border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> 새로고침</button></div></div>'),Tx=m('<button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"> </button>'),Ax=m('<div class="mt-3 rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-3"><div class="mb-2 text-[11px] font-medium text-dl-text">최근 본 회사</div> <div class="flex flex-wrap gap-1.5"></div></div>'),Nx=m('<div class="mt-3 grid grid-cols-3 gap-2"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">View</div> <div class="mt-1 text-[12px] font-medium text-dl-text"> </div></div> <div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Modules</div> <div class="mt-1 text-[12px] font-medium text-dl-text"> </div></div> <div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Selected</div> <div class="mt-1 text-[12px] font-medium text-dl-text"> </div></div></div> <div class="mt-3 grid grid-cols-2 gap-2"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Schema</div> <div class="mt-1 text-[12px] font-medium text-dl-text">표준화 계정 비교</div></div> <div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Evidence</div> <div class="mt-1 text-[12px] font-medium text-dl-text">원문 근거 보존</div></div></div>',1),Ox=m("<div> </div>"),Ix=m('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">공시 뷰어</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">회사를 선택하면 전자공시 전체를 탐색할 수 있습니다.</div></div>'),Lx=m('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">회사별 워크스페이스 준비</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">회사를 먼저 선택하면 추후 대시보드가 들어갈 Overview 슬롯과 추천 모듈 요약을 바로 볼 수 있습니다.</div></div>'),Px=m('<div class="mt-3 space-y-2"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[82%]"></div> <div class="skeleton-line w-[68%]"></div></div>'),Rx=m('<div class="rounded-xl bg-dl-bg-card/60 p-3"><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[13px] font-semibold text-dl-text"> </div> <div class="mt-1 text-[9px] text-dl-text-dim"> </div></div>'),jx=m('<div class="mt-2 text-[10px] text-dl-text-dim"> </div>'),Dx=m('<div class="flex flex-1 flex-col items-center gap-1"><div class="w-full rounded-t-md bg-gradient-to-t from-dl-primary to-dl-accent transition-all"></div> <div class="text-[9px] text-dl-text-dim"> </div></div>'),qx=m('<div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3"><div class="mb-2 text-[10px] uppercase tracking-wide text-dl-text-dim">매출 추세</div> <div class="flex items-end gap-2"></div></div>'),$x=m('<div class="mt-3 grid grid-cols-2 gap-2"></div> <!> <!>',1),Fx=m('<div class="mt-2 text-[11px] leading-relaxed text-dl-text-dim">핵심 재무 카드를 자동으로 만들 수 있는 시계열 데이터가 부족합니다. Explore에서 원본 모듈을 먼저 확인하는 흐름이 적합합니다.</div>'),Bx=m('<div class="mt-3 rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light"> </div>'),Vx=m('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/40 px-3 py-2 text-[11px] leading-relaxed text-dl-text-muted"> </div>'),Gx=m('<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2 text-[11px] text-dl-text-muted"> </div>'),Hx=m('<button class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"><div class="text-[11px] font-medium text-dl-text"> </div> <div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim"> </div></button>'),Ux=m('<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">추천 액션</div> <div class="space-y-2"></div></div>'),Wx=m('<button class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"><div class="flex items-center justify-between gap-3"><div class="min-w-0"><div class="truncate text-[12px] font-medium text-dl-text"> </div> <div class="mt-0.5 text-[10px] text-dl-text-dim"> </div></div> <span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light"> </span></div></button>'),Kx=m('<div class="space-y-3"><div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="flex items-start justify-between gap-3"><div><div class="text-[14px] font-semibold text-dl-text"> </div> <div class="mt-1 text-[10px] text-dl-text-dim"> <!> <!></div></div> <span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light">Overview</span></div> <div class="mt-3 grid grid-cols-2 gap-2"><div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3"><div class="text-[10px] text-dl-text-dim">사용 가능 데이터</div> <div class="mt-1 text-[22px] font-semibold text-dl-text"> </div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3"><div class="text-[10px] text-dl-text-dim">활성 카테고리</div> <div class="mt-1 text-[22px] font-semibold text-dl-text"> </div></div></div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 핵심 재무 카드</div> <!> <!></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">Overview 노트</div> <div class="space-y-2"></div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">읽기 포인트</div> <div class="space-y-2"></div></div> <!> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 text-[12px] font-medium text-dl-text">추천 모듈</div> <div class="space-y-2"></div></div> <div class="flex gap-2"><button class="flex-1 rounded-xl bg-dl-primary/20 px-3 py-2 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30">모듈 탐색</button> <button class="flex-1 rounded-xl border border-dl-border/60 px-3 py-2 text-[11px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-text">현재 근거 보기</button></div></div>'),Yx=m('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">아직 연결된 응답이 없습니다</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">채팅을 시작하면 이 패널에서 스냅샷, 사용한 모듈, 도구 호출, 시스템 프롬프트 요약을 함께 확인할 수 있습니다.</div></div>'),Jx=m('<div><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[18px] font-semibold text-dl-text"> </div></div>'),Xx=m('<div class="grid grid-cols-2 gap-2"></div>'),Qx=m('<span class="rounded-full bg-dl-primary/10 px-2 py-1 text-[10px] text-dl-primary-light"> </span>'),Zx=m('<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted"> </span>'),em=m('<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted"> </span>'),tm=m('<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="text-[12px] font-medium text-dl-text">현재 답변 컨텍스트</div> <div class="mt-2 flex flex-wrap gap-1.5"><!> <!> <!></div></div>'),rm=m('<div class="rounded-xl bg-dl-bg-card/60 p-2.5"><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[12px] font-semibold text-dl-text"> </div></div>'),am=m('<button data-evidence-section="snapshot" class="block w-full rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4 text-left transition-colors hover:border-dl-primary/25 hover:bg-dl-bg-darker/85"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 핵심 수치</div> <div class="grid grid-cols-2 gap-2"></div></button>'),nm=m('<button class="w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"><div class="flex items-center justify-between gap-2"><div class="text-[11px] font-medium text-dl-text"> </div> <span class="inline-flex items-center gap-1 text-[10px] text-dl-primary-light"><!> 상세</span></div> <div class="mt-1 line-clamp-3 text-[10px] leading-relaxed text-dl-text-dim"> </div></button>'),lm=m('<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">이 답변에 직접 투입된 원문/구조화 데이터입니다. 각 카드를 누르면 전문을 확인할 수 있습니다.</div> <div class="space-y-2"></div>',1),om=m('<div class="text-[11px] text-dl-text-dim">표시할 컨텍스트 데이터가 없습니다.</div>'),im=m('<button class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"><span> <!> <!></span> <span class="inline-flex items-center gap-1 text-dl-primary-light"><!> JSON</span></button>'),sm=m('<div class="space-y-1.5"></div>'),dm=m('<div class="text-[11px] text-dl-text-dim">도구 호출 기록이 없습니다.</div>'),cm=m('<button class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"><span class="min-w-0 flex-1 truncate"> <!></span> <span class="inline-flex items-center gap-1 text-dl-success"><!> 상세</span></button>'),um=m('<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">LLM이 받은 실제 툴 결과입니다. 요약만 보지 말고 상세를 열어 반환 구조를 검증할 수 있습니다.</div> <div class="space-y-1.5"></div>',1),vm=m('<div class="text-[11px] text-dl-text-dim">도구 결과 기록이 없습니다.</div>'),fm=m('<button data-evidence-section="system" class="mb-2 block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">System</div> <div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted"> </div></button>'),pm=m('<button data-evidence-section="input" class="block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">LLM Input</div> <div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted"> </div></button>'),xm=m('<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 프롬프트 투명성</div> <!> <!></div>'),mm=m('<div class="space-y-3"><!> <!> <!> <div data-evidence-section="contexts" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 근거 모듈</div> <!></div> <div data-evidence-section="tool-calls" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 도구 호출</div> <!></div> <div data-evidence-section="tool-results" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text"><!> 도구 결과</div> <!></div> <!></div>'),bm=m('<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">회사를 선택하면 탐색이 시작됩니다</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">채팅 없이도 검색 후 모듈을 열어 표, 요약, 텍스트를 직접 확인할 수 있습니다.</div></div>'),gm=m('<button class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[10px] text-dl-primary-light"> </button>'),hm=m('<div class="mb-3 flex flex-wrap gap-1.5 rounded-xl border border-dl-border/40 bg-dl-bg-card/40 p-2"><!> <button class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text">선택 해제</button></div>'),_m=m('<div class="rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light"> </div>'),ym=m('<div class="flex items-center gap-2 py-4 text-[11px] text-dl-text-dim"><!> 모듈 목록을 불러오는 중...</div>'),wm=m('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30 px-3 py-4 text-[11px] text-dl-text-dim">필터와 일치하는 모듈이 없습니다.</div>'),km=m('<button type="button">✓</button>'),Cm=m('<span class="h-4 w-4 flex-shrink-0"></span>'),Sm=m('<div><!> <button type="button" class="flex min-w-0 flex-1 items-center gap-2 text-left"><!> <div class="min-w-0 flex-1"><div class="truncate text-[11px] font-medium text-dl-text"> </div> <div class="mt-0.5 text-[10px] text-dl-text-dim"> </div></div></button></div>'),Em=m('<div class="space-y-1 border-t border-dl-border/30 px-2 pb-2 pt-1"></div>'),Mm=m('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30"><button class="flex w-full items-start gap-2 px-3 py-2.5 text-left"><!> <div class="min-w-0 flex-1"><div class="flex items-center justify-between gap-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[9px] text-dl-text-dim"> </span></div> <div class="mt-0.5 text-[10px] leading-relaxed text-dl-text-dim"> </div></div></button> <!></div>'),zm=m('<div class="p-4 text-center"><!> <div class="text-[13px] font-medium text-dl-text">모듈을 선택하세요</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">선택한 모듈은 표 미리보기와 함께 질문으로 이어갈 수 있습니다.</div></div>'),Tm=m('<div class="flex items-center gap-2 p-4 text-[11px] text-dl-text-dim"><!> </div>'),Am=m("<button><!> </button>"),Nm=m('<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[9px] text-dl-text-muted"> </span>'),Om=m('<th class="min-w-[96px] border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-right text-[10px] font-medium text-dl-text-muted"> </th>'),Im=m("<td> </td>"),Lm=m('<tr class="hover:bg-white/[0.02]"><td> </td><!></tr>'),Pm=m('<div class="max-h-[360px] overflow-auto"><table class="w-full border-collapse text-[11px]"><thead class="sticky top-0 z-[5]"><tr><th class="sticky left-0 z-[6] min-w-[180px] border-b border-r border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted">계정명</th><!></tr></thead><tbody></tbody></table></div>'),Rm=m('<th class="border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted"> </th>'),jm=m("<td> </td>"),Dm=m('<tr class="hover:bg-white/[0.02]"></tr>'),qm=m('<div class="max-h-[360px] overflow-auto"><table class="w-full border-collapse text-[11px]"><thead class="sticky top-0 z-[5]"><tr></tr></thead><tbody></tbody></table></div>'),$m=m('<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2"><div class="text-[10px] text-dl-text-dim"> </div> <div class="mt-1 text-[11px] text-dl-text-muted"> </div></div>'),Fm=m('<div class="space-y-1.5 p-4"></div>'),Bm=m('<div class="text-[11px] leading-relaxed text-dl-text-muted"> </div>'),Vm=m('<div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">핵심 문장</div> <div class="space-y-2"></div></div>'),Gm=m('<div class="p-4"><!> <pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted"> </pre></div>'),Hm=m('<div class="p-4 text-[11px] text-dl-primary-light"> </div>'),Um=m('<div class="p-4"><pre class="whitespace-pre-wrap text-[11px] text-dl-text-muted"> </pre></div>'),Wm=m('<div class="border-b border-dl-border/40 px-4 py-3"><div class="flex items-start justify-between gap-3"><div class="min-w-0"><div class="text-[13px] font-medium text-dl-text"> </div> <div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim"> </div></div> <div class="flex items-center gap-1.5"><!> <button class="rounded-lg bg-dl-success/10 px-2 py-1 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20"><!> Excel</button></div></div> <div class="mt-3 flex flex-wrap gap-1.5"></div> <div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3"><div class="text-[10px] uppercase tracking-wide text-dl-text-dim">추천 질문</div> <div class="mt-1 text-[11px] leading-relaxed text-dl-text-muted"> </div> <button class="mt-3 rounded-lg bg-dl-primary/20 px-3 py-1.5 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30">이 데이터로 질문하기</button></div></div> <!>',1),Km=m('<div class="space-y-3"><div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4"><div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2"><div class="flex items-center justify-between gap-2"><div><div class="text-[12px] font-medium text-dl-text">데이터 탐색</div> <div class="mt-0.5 text-[10px] text-dl-text-dim">카테고리를 열고 모듈을 선택하면 우측에서 바로 미리볼 수 있습니다.</div></div> <div class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] text-dl-primary-light"> </div></div></div> <div class="sticky top-0 z-[8] mb-3 rounded-xl border border-dl-border/50 bg-dl-bg-card/92 px-3 py-2 backdrop-blur-sm"><div><div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Download Actions</div> <div class="mt-1 text-[11px] text-dl-text-muted"> </div></div> <div class="mt-2 flex items-center gap-2"><button class="flex items-center gap-1 rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40"><!> 선택 다운로드</button> <button class="rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40">선택 해제</button> <button class="flex items-center gap-1 rounded-lg bg-dl-success/10 px-2.5 py-1.5 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20 disabled:opacity-40"><!> 전체 Excel</button></div></div> <!> <div class="space-y-2"><div class="relative"><!> <input type="text" placeholder="모듈 이름 또는 설명 필터" class="w-full rounded-xl border border-dl-border bg-dl-bg-card/50 py-2 pl-8 pr-3 text-[11px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"/></div> <!> <!></div></div> <div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70"><!></div></div>'),Ym=m('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4"><pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted"> </pre></div>'),Jm=m('<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted"> </pre>'),Xm=m('<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted"> </pre>'),Qm=m('<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4"><pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted"> </pre></div>'),Zm=m('<div class="fixed inset-0 z-[320] flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm" role="presentation"><div class="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-2xl border border-dl-border bg-dl-bg-card shadow-2xl shadow-black/30" role="dialog" aria-modal="true" aria-labelledby="workspace-detail-title" tabindex="-1"><div class="flex items-center justify-between border-b border-dl-border/50 px-5 py-4"><div><div id="workspace-detail-title" class="text-[14px] font-semibold text-dl-text"> </div> <div class="mt-1 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim"> </div></div> <button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="상세 데이터 닫기"><!></button></div> <div class="max-h-[calc(80vh-76px)] overflow-y-auto p-5"><!></div></div></div>'),eb=m('<div class="surface-panel flex h-full min-h-0 flex-col bg-dl-bg-card/92 backdrop-blur-sm"><div class="border-b border-dl-border/60 px-4 py-3"><div class="flex items-center justify-between gap-3"><div class="min-w-0"><div class="flex items-center gap-2 text-[14px] font-semibold text-dl-text"><!> <span>Workspace</span></div> <div class="mt-0.5 text-[11px] text-dl-text-dim">표준화된 계정, 서술형 텍스트, 원문 근거를 한 화면에서 검증하는 분석 워크벤치</div></div> <!></div> <div class="relative mt-3"><!> <input type="text" placeholder="종목명 또는 종목코드 검색" class="w-full rounded-xl border border-dl-border bg-dl-bg-darker py-2.5 pl-9 pr-9 text-[12px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"/> <!></div> <!> <!> <div class="mt-3 grid grid-cols-4 gap-1.5 rounded-xl bg-dl-bg-darker p-1"><button>공시</button> <button>Overview</button> <button>Explore</button> <button>Evidence</button></div> <!></div> <div class="flex-1 overflow-y-auto p-4"><!> <!></div></div> <!>',1);function bs(e,t){fa(t,!0);let a=St(t,"selectedCompany",3,null),n=St(t,"recentCompanies",19,()=>[]),l=St(t,"activeTab",3,"explore"),o=St(t,"evidenceMessage",3,null),s=St(t,"activeEvidenceSection",3,null),d=St(t,"selectedEvidenceIndex",3,null),v=D(""),x=D(yt([])),g=D(!1),k=null,C=D(null),R=D(!1),T=D(yt(new Set)),I=D(null),y=D(null),M=D(!1),F=D(!1),H=D(!0),_=D(yt(new Set)),L=D(null),U=D(null),re=D(!1),E=D(yt([])),Y=D(yt([])),X=D(""),Ce=D(yt([])),lt=D(yt([])),he=D(""),fe=D(""),W=D(""),Ae=D(!1),ot=D(null),ge=D(null),wt=D(null),ae=D(yt([]));const qt={finance:"재무제표",report:"정기보고서",disclosure:"공시 서술",notes:"K-IFRS 주석",analysis:"분석",raw:"원본 데이터"},Ne={finance:"실적, 재무상태, 현금흐름을 빠르게 확인합니다.",report:"정기보고서에서 구조화된 회사 정보를 확인합니다.",disclosure:"사업, MD&A, 원재료 등 서술형 공시를 읽습니다.",notes:"주석 계정과 세부 항목을 깊게 확인합니다.",analysis:"파생 분석이나 인사이트 결과를 확인합니다.",raw:"원본 데이터나 가공 전 결과를 검증합니다."};function h(u){return qt[u]||u}function P(u){return Ne[u]||"관련 데이터를 탐색합니다."}function B(u){return`${u.filter(z=>z.available).length}/${u.length}`}function Q(u){return u.dataType==="timeseries"?"시계열 비교에 적합한 구조화 데이터":u.dataType==="table"||u.dataType==="dataframe"?"행·열 기준으로 직접 확인 가능한 표 데이터":u.dataType==="dict"?"핵심 필드를 빠르게 점검하는 요약 데이터":u.dataType==="text"?"원문 또는 긴 서술 데이터를 직접 읽는 모듈":"구조화된 모듈 데이터"}function pe(u){var b,z,j,q;return u.category==="finance"?`${((b=a())==null?void 0:b.corpName)||"이 회사"}의 ${u.label}에서 가장 중요한 변화만 요약해줘`:u.category==="notes"?`${((z=a())==null?void 0:z.corpName)||"이 회사"}의 ${u.label}에서 주의할 점을 설명해줘`:u.category==="disclosure"?`${((j=a())==null?void 0:j.corpName)||"이 회사"}의 ${u.label} 핵심 내용을 요약해줘`:`${((q=a())==null?void 0:q.corpName)||"이 회사"}의 ${u.label} 데이터를 바탕으로 핵심 포인트를 정리해줘`}function xe(u){var b,z;return!((z=(b=r(y))==null?void 0:b.meta)!=null&&z.labels)||!r(H)?u:r(y).meta.labels[u]||u}function le(u){var b,z;return(z=(b=r(y))==null?void 0:b.meta)!=null&&z.levels&&r(y).meta.levels[u]||1}function ct(){var u,b,z;return(b=(u=r(y))==null?void 0:u.meta)!=null&&b.unit?r(y).meta.unit:(z=r(y))!=null&&z.unit?r(y).unit:""}function Et(){var u,b;return!!((b=(u=r(y))==null?void 0:u.meta)!=null&&b.labels)}function Je(){var u;return(u=r(y))!=null&&u.columns?r(y).columns.filter(b=>b!=="계정명"):[]}function ze(u){return Number.isInteger(u)&&u>=1900&&u<=2100}function Mt(u){if(u==null)return"-";if(typeof u!="number")return String(u);if(u===0)return"0";const b=Math.abs(u),z=u<0?"-":"";return b>=1e12?`${z}${(b/1e12).toLocaleString("ko-KR",{maximumFractionDigits:1})}조`:b>=1e8?`${z}${Math.round(b/1e8).toLocaleString("ko-KR")}억`:b>=1e4?`${z}${Math.round(b/1e4).toLocaleString("ko-KR")}만`:u.toLocaleString("ko-KR")}function Se(u,b){if(u==null)return"-";if(typeof u=="number"){if(ze(u))return String(u);if(b==="원"||b==="백만원")return b==="백만원"&&(u*=1e6),Mt(u);if(Number.isInteger(u)&&Math.abs(u)>=1e3)return u.toLocaleString("ko-KR");if(!Number.isInteger(u))return u.toLocaleString("ko-KR",{maximumFractionDigits:2})}return String(u)}function Ie(u){var b,z,j;return u?u.type==="table"?[`${(u.totalRows||((b=u.rows)==null?void 0:b.length)||0).toLocaleString()}개 행`,`${(((z=u.columns)==null?void 0:z.length)||0).toLocaleString()}개 열`,u.truncated?"일부 행만 미리보기":"전체 미리보기 범위"]:u.type==="text"?[`${(((j=u.text)==null?void 0:j.length)||0).toLocaleString()}자 텍스트`,u.truncated?"긴 텍스트 일부만 노출":"본문 전체 미리보기"]:u.type==="dict"?[`${Object.keys(u.data||{}).length.toLocaleString()}개 필드`,"요약 필드 구조"]:["구조화 데이터","원본 확인 가능"]:[]}function Le(u){return u?u.split(/\n+/).map(b=>b.trim()).filter(Boolean).filter(b=>b.length>18).slice(0,3):[]}async function zt(u){if(!(u!=null&&u.stockCode)){c(C,null),c(U,null),c(E,[],!0),c(Y,[],!0),c(Ce,[],!0),c(W,"");return}c(R,!0),c(I,null),c(y,null),c(_,new Set,!0);try{c(C,await Xu(u.stockCode),!0);const b=Object.keys(r(C).categories||{});c(T,new Set(b.slice(0,2)),!0),c(L,u.stockCode,!0),c(W,"")}catch{c(C,null),c(W,"데이터 소스 목록을 불러오지 못했습니다. 다시 시도해 주세요.")}c(R,!1)}na(()=>{var b;const u=((b=a())==null?void 0:b.stockCode)||null;!u||u===r(L)||zt(a())}),na(()=>{var b;!((b=a())!=null&&b.stockCode)||!r(C)||qa(a(),r(C))});function Ot(){const u=r(v).trim();if(k&&clearTimeout(k),u.length<2){c(x,[],!0),c(g,!1);return}c(g,!0),k=setTimeout(async()=>{var b;try{const z=await yd(u);c(x,((b=z.results)==null?void 0:b.slice(0,8))||[],!0)}catch{c(x,[],!0)}c(g,!1)},250)}async function mt(u){var b,z;(b=t.onSelectCompany)==null||b.call(t,u),c(v,""),c(x,[],!0),(z=t.onChangeTab)==null||z.call(t,"overview"),await zt(u)}function Fe(){var u,b;(u=t.onSelectCompany)==null||u.call(t,null),c(v,""),c(x,[],!0),c(C,null),c(I,null),c(y,null),c(L,null),c(U,null),c(E,[],!0),c(Y,[],!0),c(Ce,[],!0),c(fe,""),c(_,new Set,!0),(b=t.onChangeTab)==null||b.call(t,"explore")}function bt(u){const b=new Set(r(T));b.has(u)?b.delete(u):b.add(u),c(T,b,!0)}async function Tt(u){var b,z;if(!(!u.available||!((b=a())!=null&&b.stockCode))){c(I,u,!0),(z=t.onChangeTab)==null||z.call(t,"explore"),c(M,!0),c(y,null);try{c(y,await Go(a().stockCode,u.name,200),!0)}catch(j){c(y,{type:"error",error:j.message},!0)}c(M,!1)}}async function $e(u=null){var b,z;if(a()){c(F,!0);try{await Ju(a().stockCode,u);const j=u!=null&&u.length?`선택한 ${u.length}개 모듈을 다운로드했습니다.`:"전체 Excel 다운로드를 시작했습니다.";rt("success",j),(b=t.onNotify)==null||b.call(t,j,"success")}catch{const j="Excel 다운로드를 시작하지 못했습니다. 다시 시도해 주세요.";rt("error",j),(z=t.onNotify)==null||z.call(t,j)}c(F,!1)}}function Be(u){if(!(u!=null&&u.available))return;const b=new Set(r(_));b.has(u.name)?b.delete(u.name):b.add(u.name),c(_,b,!0)}function Te(){var u;!a()||!r(I)||(u=t.onAskAboutModule)==null||u.call(t,a(),r(I),r(y))}function rt(u,b){c(ot,{type:u,text:b},!0),setTimeout(()=>{var z;((z=r(ot))==null?void 0:z.text)===b&&c(ot,null)},2600)}let ie=se(()=>{var z;const u=r(he).trim().toLowerCase(),b=Object.entries(((z=r(C))==null?void 0:z.categories)||{});return u?b.map(([j,q])=>[j,q.filter(G=>`${G.label} ${G.name} ${G.description||""}`.toLowerCase().includes(u))]).filter(([,j])=>j.length>0):b}),ne=se(()=>{var u;return((u=r(C))==null?void 0:u.availableSources)||0}),be=se(()=>r(ie).filter(([,u])=>u.some(b=>b.available)).length),Ee=se(()=>r(ie).flatMap(([b,z])=>z.filter(j=>j.available).map(j=>({...j,category:b}))).slice(0,5)),Xe=se(()=>{var u;return((u=o())==null?void 0:u.contexts)||[]}),Qe=se(()=>{var u;return(((u=o())==null?void 0:u.toolEvents)||[]).filter(b=>b.type==="call")}),gt=se(()=>{var u;return(((u=o())==null?void 0:u.toolEvents)||[]).filter(b=>b.type==="result")}),$t=se(()=>{var b,z,j,q;const u=[];return(j=(z=(b=o())==null?void 0:b.snapshot)==null?void 0:z.items)!=null&&j.length&&u.push({label:"핵심 수치",value:o().snapshot.items.length,tone:"success"}),r(Xe).length&&u.push({label:"컨텍스트",value:r(Xe).length,tone:"default"}),r(Qe).length&&u.push({label:"툴 호출",value:r(Qe).length,tone:"accent"}),r(gt).length&&u.push({label:"툴 결과",value:r(gt).length,tone:"success"}),(q=o())!=null&&q.systemPrompt&&u.push({label:"프롬프트",value:1,tone:"default"}),u}),Vt=se(()=>Ie(r(y))),ir=se(()=>{var u;return((u=r(y))==null?void 0:u.type)==="text"?Le(r(y).text):[]}),ht=se(()=>r(he).trim().length>0),Pe=se(()=>[...r(_)]),Ft=se(()=>{var b;const u=new Map(Object.values(((b=r(C))==null?void 0:b.categories)||{}).flat().map(z=>[z.name,z]));return r(Pe).map(z=>u.get(z)).filter(Boolean)});function Z(u){var b;(b=t.onChangeTab)==null||b.call(t,u)}function Ue(u,b,z){c(ge,{type:u,payload:b,title:z},!0)}function Pt(){c(ge,null)}function kt(u,b){for(const z of b)if(u.has(z)&&u.get(z).available)return u.get(z);return null}function Bt(u,b){var q,G;if(!((q=u==null?void 0:u.rows)!=null&&q.length)||!((G=u==null?void 0:u.columns)!=null&&G.length))return null;const z=u.columns.filter(ce=>ce!=="계정명");if(!z.length)return null;const j=z[z.length-1];for(const ce of u.rows){const Oe=ce.계정명;if(b.includes(Oe))return{value:ce[j],period:j}}return null}function _r(u,b){var Oe,_t,K,oe;const z=[],j=Bt(u,["revenue","sales"]),q=Bt(u,["operating_income"]),G=Bt(u,["net_income","profit_loss"]),ce=Bt(b,["total_assets"]);return j&&z.push({label:"최근 매출",value:Se(j.value,((Oe=u==null?void 0:u.meta)==null?void 0:Oe.unit)||(u==null?void 0:u.unit)||"원"),period:j.period}),q&&z.push({label:"최근 영업이익",value:Se(q.value,((_t=u==null?void 0:u.meta)==null?void 0:_t.unit)||(u==null?void 0:u.unit)||"원"),period:q.period}),G&&z.push({label:"최근 순이익",value:Se(G.value,((K=u==null?void 0:u.meta)==null?void 0:K.unit)||(u==null?void 0:u.unit)||"원"),period:G.period}),ce&&z.push({label:"최근 총자산",value:Se(ce.value,((oe=b==null?void 0:b.meta)==null?void 0:oe.unit)||(b==null?void 0:b.unit)||"원"),period:ce.period}),z}function vr(u,b){var Oe,_t;if(!((Oe=u==null?void 0:u.rows)!=null&&Oe.length)||!((_t=u==null?void 0:u.columns)!=null&&_t.length))return[];const z=u.rows.find(K=>b.includes(K.계정명));if(!z)return[];const q=u.columns.filter(K=>K!=="계정명").slice(-5).map(K=>({label:K,value:typeof z[K]=="number"?z[K]:null})),G=q.filter(K=>typeof K.value=="number").map(K=>Math.abs(K.value)),ce=Math.max(...G,0);return q.map(K=>({...K,ratio:ce>0&&typeof K.value=="number"?Math.max(8,Math.round(Math.abs(K.value)/ce*100)):0}))}function Nr(u,b,z,j){var ce,Oe,_t,K;const q=[],G=Object.entries(b.categories||{}).filter(([,oe])=>oe.some(qe=>qe.available)).map(([oe])=>h(oe));return G.length>0&&q.push(`활성 카테고리 ${G.slice(0,3).join(", ")}`),(ce=z.get("dividend"))!=null&&ce.available&&q.push("배당 데이터 확인 가능"),(Oe=z.get("majorHolder"))!=null&&Oe.available&&q.push("최대주주 데이터 확인 가능"),((_t=z.get("business"))!=null&&_t.available||(K=z.get("mdna"))!=null&&K.available)&&q.push("서술형 사업/리스크 공시 탐색 가능"),j.length||q.push("핵심 재무 카드는 원본 표 탐색 후 질문으로 이어가는 흐름에 최적화됨"),u!=null&&u.market&&q.push(`${u.market} 상장사`),q.slice(0,4)}function Vr(u){var z,j;const b=[];return kt(u,["annual.IS","IS","fsSummary"])&&b.push({label:"실적 구조 보기",description:"표준화된 계정을 바로 열어 비교 가능한 숫자 구조를 확인합니다.",tab:"explore"}),((z=u.get("business"))!=null&&z.available||(j=u.get("mdna"))!=null&&j.available)&&b.push({label:"사업/리스크 읽기",description:"서술형 공시 텍스트와 원문 근거를 같이 훑습니다.",tab:"explore"}),b.push({label:"현재 근거 보기",description:"채팅에서 사용된 스냅샷, 컨텍스트, 툴 결과를 검증합니다.",tab:"evidence"}),b.slice(0,3)}async function qa(u,b){if(!(u!=null&&u.stockCode)||!b)return;c(re,!0),c(fe,"");const z=new Map(Object.values(b.categories||{}).flat().map(G=>[G.name,G])),j=kt(z,["annual.IS","IS","fsSummary"]),q=kt(z,["annual.BS","BS"]);try{const[G,ce,Oe]=await Promise.all([Qu(u.stockCode).catch(()=>u),j?Go(u.stockCode,j.name,80).catch(()=>null):Promise.resolve(null),q?Go(u.stockCode,q.name,80).catch(()=>null):Promise.resolve(null)]);c(U,{...u,...G||{}},!0),c(E,_r(ce,Oe),!0),c(Y,Nr(r(U),b,z,r(E)),!0),c(Ce,vr(ce,["revenue","sales"]),!0),c(X,[j==null?void 0:j.label,q==null?void 0:q.label].filter(Boolean).join(" / "),!0),c(ae,Vr(z),!0),c(lt,[r(E)[0]?`${r(E)[0].label} 기준 최근 관측 시점은 ${r(E)[0].period}입니다.`:"핵심 재무 카드는 원본 시계열이 있을 때 자동 생성됩니다.",r(Ce).length>1?"추세 막대는 최근 5개 시점의 절대 규모를 기준으로 시각화합니다.":"추세 데이터가 충분하지 않으면 Explore에서 원본 표를 먼저 확인하는 편이 낫습니다.",r(X)?`현재 Overview는 ${r(X)} 모듈을 기준으로 조립되었습니다.`:"현재 Overview는 기본 회사 정보와 사용 가능한 모듈 중심으로 조립되었습니다."],!0)}catch{c(U,u,!0),c(E,[],!0),c(Y,["회사 기본 정보만 확인할 수 있습니다."],!0),c(Ce,[],!0),c(X,""),c(fe,"Overview 데이터를 만들지 못했습니다. Explore에서 원본 모듈을 확인해 주세요."),c(ae,[],!0),c(lt,["Overview 조립 실패로 인해 원본 모듈 탐색 흐름이 우선입니다."],!0)}c(re,!1)}async function Ma(){var u;typeof navigator>"u"||!navigator.clipboard||(await navigator.clipboard.writeText(window.location.href),c(Ae,!0),rt("success","워크스페이스 링크를 복사했습니다."),(u=t.onNotify)==null||u.call(t,"워크스페이스 링크를 복사했습니다.","success"),setTimeout(()=>{c(Ae,!1)},1500))}na(()=>{l()!=="evidence"||!s()||!o()||requestAnimationFrame(()=>{var u;if((u=document.querySelector(`[data-evidence-section="${s()}"]`))==null||u.scrollIntoView({block:"start",behavior:"smooth"}),s()==="snapshot"&&o().snapshot){c(ge,{type:"snapshot",payload:o().snapshot,title:"핵심 수치"},!0);return}if(s()==="contexts"&&r(Xe).length>0){const b=r(Xe)[d()??0];b&&c(ge,{type:"context",payload:b,title:b.label||b.module||"컨텍스트"},!0);return}if(s()==="tool-calls"&&r(Qe).length>0){const b=r(Qe)[d()??0];b&&c(ge,{type:"tool-call",payload:b,title:`${b.name} 호출`},!0);return}if(s()==="tool-results"&&r(gt).length>0){const b=r(gt)[d()??0];b&&c(ge,{type:"tool-result",payload:b,title:`${b.name} 결과`},!0);return}if(s()==="system"&&o().systemPrompt){c(ge,{type:"system",payload:o().systemPrompt,title:"System Prompt"},!0);return}s()==="input"&&o().userContent&&c(ge,{type:"user",payload:o().userContent,title:"LLM Input"},!0)})}),na(()=>{!r(ge)||!r(wt)||requestAnimationFrame(()=>{var u;return(u=r(wt))==null?void 0:u.focus()})});var xa=eb(),hn=te(xa),Hn=i(hn),Dl=i(Hn),xl=i(Dl),ko=i(xl),ql=i(ko);Cr(ql,{size:16,class:"text-dl-primary-light"});var Co=f(xl,2);{var $l=u=>{var b=Sx(),z=i(b);Xn(z,{size:16}),$("click",b,()=>{var j;return(j=t.onClose)==null?void 0:j.call(t)}),p(u,b)};A(Co,u=>{t.onClose&&u($l)})}var Fl=f(Dl,2),Un=i(Fl);Bn(Un,{size:14,class:"pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim"});var Wn=f(Un,2),So=f(Wn,2);{var Eo=u=>{Tr(u,{size:14,class:"absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim"})};A(So,u=>{r(g)&&u(Eo)})}var Bl=f(Fl,2);{var Mo=u=>{var b=Mx();we(b,21,()=>r(x),ye,(z,j)=>{var q=Ex(),G=i(q),ce=i(G),Oe=f(G,2),_t=i(Oe),K=i(_t),oe=f(_t,2),qe=i(oe),fr=f(Oe,2);vi(fr,{size:14,class:"flex-shrink-0 text-dl-text-dim"}),N(()=>{S(ce,r(j).corpName[0]),S(K,r(j).corpName),S(qe,`${r(j).stockCode??""} · ${(r(j).market||"미분류")??""}`)}),$("click",q,()=>mt(r(j))),p(z,q)}),p(u,b)};A(Bl,u=>{r(x).length>0&&u(Mo)})}var Vl=f(Bl,2);{var zo=u=>{var b=zx(),z=i(b),j=i(z),q=i(j),G=i(q),ce=f(q,2),Oe=i(ce),_t=f(Oe);{var K=Gt=>{var Ut=sa();N(()=>S(Ut,`· ${a().market??""}`)),p(Gt,Ut)};A(_t,Gt=>{a().market&&Gt(K)})}var oe=f(_t,2);{var qe=Gt=>{var Ut=sa();N(()=>S(Ut,`· ${r(ne)??""}개 데이터`)),p(Gt,Ut)};A(oe,Gt=>{r(ne)&&Gt(qe)})}var fr=f(j,2),Rt=f(z,2),er=i(Rt),yr=i(er);gf(yr,{size:10,class:"mr-1 inline"});var It=f(yr),ke=f(er,2),Qt=i(ke);Cf(Qt,{size:10,class:"mr-1 inline"}),N(()=>{var Gt;S(G,a().corpName||a().company||((Gt=r(U))==null?void 0:Gt.corpName)||a().stockCode),S(Oe,`${a().stockCode??""} `),S(It,` ${r(Ae)?"링크 복사됨":"링크 복사"}`)}),$("click",fr,Fe),$("click",er,Ma),$("click",ke,()=>zt(a())),p(u,b)},To=u=>{var b=Ax(),z=f(i(b),2);we(z,21,n,ye,(j,q)=>{var G=Tx(),ce=i(G);N(()=>S(ce,`${(r(q).corpName||r(q).company)??""} · ${r(q).stockCode??""}`)),$("click",G,()=>mt(r(q))),p(j,G)}),p(u,b)};A(Vl,u=>{a()?u(zo):n().length>0&&u(To,1)})}var Gl=f(Vl,2),Kn=i(Gl),ml=f(Kn,2),bl=f(ml,2),Hl=f(bl,2),Ao=f(Gl,2);{var No=u=>{var b=Nx(),z=te(b),j=i(z),q=f(i(j),2),G=i(q),ce=f(j,2),Oe=f(i(ce),2),_t=i(Oe),K=f(ce,2),oe=f(i(K),2),qe=i(oe);N(()=>{S(G,l()==="sections"?"공시":l()==="overview"?"Overview":l()==="explore"?"Explore":"Evidence"),S(_t,r(ne)),S(qe,r(Pe).length)}),p(u,b)};A(Ao,u=>{a()&&u(No)})}var Ul=f(Hn,2),Wl=i(Ul);{var Kl=u=>{var b=Ox(),z=i(b);N(j=>{Ge(b,1,j),S(z,r(ot).text)},[()=>ut(vt("mb-3 rounded-xl border px-3 py-2 text-[10px]",r(ot).type==="success"?"border-dl-success/30 bg-dl-success/10 text-dl-success":"border-dl-primary/20 bg-dl-primary/[0.05] text-dl-primary-light"))]),p(u,b)};A(Wl,u=>{r(ot)&&u(Kl)})}var Oo=f(Wl,2);{var Yl=u=>{var b=Me(),z=te(b);{var j=G=>{Cx(G,{get stockCode(){return a().stockCode},get corpName(){return a().corpName}})},q=G=>{var ce=Ix(),Oe=i(ce);Sf(Oe,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),p(G,ce)};A(z,G=>{a()?G(j):G(q,-1)})}p(u,b)},Io=u=>{var b=Me(),z=te(b);{var j=G=>{var ce=Lx(),Oe=i(ce);Cr(Oe,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),p(G,ce)},q=G=>{var ce=Kx(),Oe=i(ce),_t=i(Oe),K=i(_t),oe=i(K),qe=i(oe),fr=f(oe,2),Rt=i(fr),er=f(Rt);{var yr=ve=>{var me=sa();N(()=>{var De;return S(me,`· ${(((De=r(U))==null?void 0:De.market)||a().market)??""}`)}),p(ve,me)};A(er,ve=>{var me;((me=r(U))!=null&&me.market||a().market)&&ve(yr)})}var It=f(er,2);{var ke=ve=>{var me=sa();N(()=>{var De;return S(me,`· ${(((De=r(U))==null?void 0:De.sector)||a().sector)??""}`)}),p(ve,me)};A(It,ve=>{var me;((me=r(U))!=null&&me.sector||a().sector)&&ve(ke)})}var Qt=f(_t,2),Gt=i(Qt),Ut=f(i(Gt),2),Ur=i(Ut),la=f(Gt,2),Ja=f(i(la),2),$a=i(Ja),ma=f(Oe,2),ba=i(ma),Xa=i(ba);Mf(Xa,{size:13,class:"text-dl-accent"});var Fa=f(ba,2);{var Ba=ve=>{var me=Px();p(ve,me)},Qa=ve=>{var me=$x(),De=te(me);we(De,21,()=>r(E),ye,(pr,dr)=>{var Fr=Rx(),Qr=i(Fr),Gr=i(Qr),Zr=f(Qr,2),ea=i(Zr),at=f(Zr,2),At=i(at);N(()=>{S(Gr,r(dr).label),S(ea,r(dr).value),S(At,r(dr).period)}),p(pr,Fr)});var sr=f(De,2);{var ar=pr=>{var dr=jx(),Fr=i(dr);N(()=>S(Fr,`출처: ${r(X)??""}`)),p(pr,dr)};A(sr,pr=>{r(X)&&pr(ar)})}var Or=f(sr,2);{var $r=pr=>{var dr=qx(),Fr=f(i(dr),2);we(Fr,21,()=>r(Ce),ye,(Qr,Gr)=>{var Zr=Dx(),ea=i(Zr),at=f(ea,2),At=i(at);N(Yt=>{so(ea,`height: ${r(Gr).ratio||8}px`),ka(ea,"title",Yt),S(At,r(Gr).label)},[()=>r(Gr).value===null?"-":Se(r(Gr).value,"원")]),p(Qr,Zr)}),p(pr,dr)};A(Or,pr=>{r(Ce).length>0&&pr($r)})}p(ve,me)},_n=ve=>{var me=Fx();p(ve,me)};A(Fa,ve=>{r(re)?ve(Ba):r(E).length>0?ve(Qa,1):ve(_n,-1)})}var Za=f(Fa,2);{var Ve=ve=>{var me=Bx(),De=i(me);N(()=>S(De,r(fe))),p(ve,me)};A(Za,ve=>{r(fe)&&ve(Ve)})}var Ze=f(ma,2),Wt=f(i(Ze),2);we(Wt,21,()=>r(lt),ye,(ve,me)=>{var De=Vx(),sr=i(De);N(()=>S(sr,r(me))),p(ve,De)});var jt=f(Ze,2),Ct=f(i(jt),2);we(Ct,21,()=>r(Y),ye,(ve,me)=>{var De=Gx(),sr=i(De);N(()=>S(sr,r(me))),p(ve,De)});var Kt=f(jt,2);{var rr=ve=>{var me=Ux(),De=f(i(me),2);we(De,21,()=>r(ae),ye,(sr,ar)=>{var Or=Hx(),$r=i(Or),pr=i($r),dr=f($r,2),Fr=i(dr);N(()=>{S(pr,r(ar).label),S(Fr,r(ar).description)}),$("click",Or,()=>Z(r(ar).tab)),p(sr,Or)}),p(ve,me)};A(Kt,ve=>{r(ae).length>0&&ve(rr)})}var tr=f(Kt,2),dt=f(i(tr),2);we(dt,21,()=>r(Ee),ye,(ve,me)=>{var De=Wx(),sr=i(De),ar=i(sr),Or=i(ar),$r=i(Or),pr=f(Or,2),dr=i(pr),Fr=f(ar,2),Qr=i(Fr);N((Gr,Zr)=>{S($r,r(me).label),S(dr,Gr),S(Qr,Zr)},[()=>Q(r(me)),()=>h(r(me).category)]),$("click",De,()=>Tt(r(me))),p(ve,De)});var _e=f(tr,2),J=i(_e),je=f(J,2);N(()=>{var ve,me;S(qe,((ve=r(U))==null?void 0:ve.corpName)||a().corpName||a().company||a().stockCode),S(Rt,`${(((me=r(U))==null?void 0:me.stockCode)||a().stockCode)??""} `),S(Ur,r(ne)),S($a,r(be))}),$("click",J,()=>Z("explore")),$("click",je,()=>Z("evidence")),p(G,ce)};A(z,G=>{a()?G(q,-1):G(j)})}p(u,b)},Lo=u=>{var b=Me(),z=te(b);{var j=G=>{var ce=Yx(),Oe=i(ce);Cr(Oe,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),p(G,ce)},q=G=>{var ce=mm(),Oe=i(ce);{var _t=Ve=>{var Ze=Xx();we(Ze,21,()=>r($t),ye,(Wt,jt)=>{var Ct=Jx(),Kt=i(Ct),rr=i(Kt),tr=f(Kt,2),dt=i(tr);N(_e=>{Ge(Ct,1,_e),S(rr,r(jt).label),S(dt,r(jt).value)},[()=>ut(vt("rounded-2xl border px-3 py-3",r(jt).tone==="success"?"border-dl-success/20 bg-dl-success/[0.06]":r(jt).tone==="accent"?"border-dl-accent/20 bg-dl-accent/[0.06]":"border-dl-border/40 bg-dl-bg-darker/70"))]),p(Wt,Ct)}),p(Ve,Ze)};A(Oe,Ve=>{r($t).length>0&&Ve(_t)})}var K=f(Oe,2);{var oe=Ve=>{var Ze=tm(),Wt=f(i(Ze),2),jt=i(Wt);{var Ct=dt=>{var _e=Qx(),J=i(_e);N(()=>S(J,o().meta.company)),p(dt,_e)};A(jt,dt=>{var _e;(_e=o().meta)!=null&&_e.company&&dt(Ct)})}var Kt=f(jt,2);{var rr=dt=>{var _e=Zx(),J=i(_e);N(()=>S(J,typeof o().meta.dataYearRange=="string"?o().meta.dataYearRange:`${o().meta.dataYearRange.min_year}~${o().meta.dataYearRange.max_year}년`)),p(dt,_e)};A(Kt,dt=>{var _e;(_e=o().meta)!=null&&_e.dataYearRange&&dt(rr)})}var tr=f(Kt,2);we(tr,17,()=>{var dt;return((dt=o().meta)==null?void 0:dt.includedModules)||[]},ye,(dt,_e)=>{var J=em(),je=i(J);N(()=>S(je,r(_e))),p(dt,J)}),p(Ve,Ze)};A(K,Ve=>{var Ze,Wt;((Ze=o().meta)!=null&&Ze.company||(Wt=o().meta)!=null&&Wt.dataYearRange)&&Ve(oe)})}var qe=f(K,2);{var fr=Ve=>{var Ze=am(),Wt=i(Ze),jt=i(Wt);Cr(jt,{size:13,class:"text-dl-success"});var Ct=f(Wt,2);we(Ct,21,()=>o().snapshot.items,ye,(Kt,rr)=>{var tr=rm(),dt=i(tr),_e=i(dt),J=f(dt,2),je=i(J);N(()=>{S(_e,r(rr).label),S(je,r(rr).value)}),p(Kt,tr)}),$("click",Ze,()=>Ue("snapshot",o().snapshot,"핵심 수치")),p(Ve,Ze)};A(qe,Ve=>{var Ze,Wt;((Wt=(Ze=o().snapshot)==null?void 0:Ze.items)==null?void 0:Wt.length)>0&&Ve(fr)})}var Rt=f(qe,2),er=i(Rt),yr=i(er);Cr(yr,{size:13,class:"text-dl-accent"});var It=f(er,2);{var ke=Ve=>{var Ze=lm(),Wt=f(te(Ze),2);we(Wt,21,()=>r(Xe),ye,(jt,Ct)=>{var Kt=nm(),rr=i(Kt),tr=i(rr),dt=i(tr),_e=f(tr,2),J=i(_e);fi(J,{size:11});var je=f(rr,2),ve=i(je);N(()=>{S(dt,r(Ct).label||r(Ct).module),S(ve,r(Ct).text)}),$("click",Kt,()=>Ue("context",r(Ct),r(Ct).label||r(Ct).module||"컨텍스트")),p(jt,Kt)}),p(Ve,Ze)},Qt=Ve=>{var Ze=om();p(Ve,Ze)};A(It,Ve=>{r(Xe).length>0?Ve(ke):Ve(Qt,-1)})}var Gt=f(Rt,2),Ut=i(Gt),Ur=i(Ut);pi(Ur,{size:13,class:"text-dl-primary-light"});var la=f(Ut,2);{var Ja=Ve=>{var Ze=sm();we(Ze,21,()=>r(Qe),ye,(Wt,jt)=>{var Ct=im(),Kt=i(Ct),rr=i(Kt),tr=f(rr);{var dt=me=>{var De=sa();N(()=>S(De,`· ${r(jt).arguments.module??""}`)),p(me,De)};A(tr,me=>{var De;(De=r(jt).arguments)!=null&&De.module&&me(dt)})}var _e=f(tr,2);{var J=me=>{var De=sa();N(()=>S(De,`· ${r(jt).arguments.keyword??""}`)),p(me,De)};A(_e,me=>{var De;(De=r(jt).arguments)!=null&&De.keyword&&me(J)})}var je=f(Kt,2),ve=i(je);Rn(ve,{size:11}),N(()=>S(rr,`${r(jt).name??""} `)),$("click",Ct,()=>Ue("tool-call",r(jt),`${r(jt).name} 호출`)),p(Wt,Ct)}),p(Ve,Ze)},$a=Ve=>{var Ze=dm();p(Ve,Ze)};A(la,Ve=>{r(Qe).length>0?Ve(Ja):Ve($a,-1)})}var ma=f(Gt,2),ba=i(ma),Xa=i(ba);Rn(Xa,{size:13,class:"text-dl-success"});var Fa=f(ba,2);{var Ba=Ve=>{var Ze=um(),Wt=f(te(Ze),2);we(Wt,21,()=>r(gt),ye,(jt,Ct)=>{var Kt=cm(),rr=i(Kt),tr=i(rr),dt=f(tr);{var _e=ve=>{var me=sa();N(De=>S(me,`· ${De??""}`),[()=>r(Ct).result.slice(0,80)]),p(ve,me)};A(dt,ve=>{typeof r(Ct).result=="string"&&ve(_e)})}var J=f(rr,2),je=i(J);fi(je,{size:11}),N(()=>S(tr,`${r(Ct).name??""} `)),$("click",Kt,()=>Ue("tool-result",r(Ct),`${r(Ct).name} 결과`)),p(jt,Kt)}),p(Ve,Ze)},Qa=Ve=>{var Ze=vm();p(Ve,Ze)};A(Fa,Ve=>{r(gt).length>0?Ve(Ba):Ve(Qa,-1)})}var _n=f(ma,2);{var Za=Ve=>{var Ze=xm(),Wt=i(Ze),jt=i(Wt);no(jt,{size:13,class:"text-dl-accent-light"});var Ct=f(Wt,2);{var Kt=dt=>{var _e=fm(),J=f(i(_e),2),je=i(J);N(()=>S(je,o().systemPrompt)),$("click",_e,()=>Ue("system",o().systemPrompt,"System Prompt")),p(dt,_e)};A(Ct,dt=>{o().systemPrompt&&dt(Kt)})}var rr=f(Ct,2);{var tr=dt=>{var _e=pm(),J=f(i(_e),2),je=i(J);N(()=>S(je,o().userContent)),$("click",_e,()=>Ue("user",o().userContent,"LLM Input")),p(dt,_e)};A(rr,dt=>{o().userContent&&dt(tr)})}p(Ve,Ze)};A(_n,Ve=>{(o().systemPrompt||o().userContent)&&Ve(Za)})}p(G,ce)};A(z,G=>{o()?G(q,-1):G(j)})}p(u,b)},Po=u=>{var b=Me(),z=te(b);{var j=G=>{var ce=bm(),Oe=i(ce);Cr(Oe,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),p(G,ce)},q=G=>{var ce=Km(),Oe=i(ce),_t=i(Oe),K=i(_t),oe=f(i(K),2),qe=i(oe),fr=f(_t,2),Rt=i(fr),er=f(i(Rt),2),yr=i(er),It=f(Rt,2),ke=i(It),Qt=i(ke);{var Gt=J=>{Tr(J,{size:11,class:"animate-spin"})},Ut=J=>{jn(J,{size:11})};A(Qt,J=>{r(F)&&r(Pe).length>0?J(Gt):J(Ut,-1)})}var Ur=f(ke,2),la=f(Ur,2),Ja=i(la);{var $a=J=>{Tr(J,{size:11,class:"animate-spin"})},ma=J=>{jn(J,{size:11})};A(Ja,J=>{r(F)&&r(Pe).length===0?J($a):J(ma,-1)})}var ba=f(fr,2);{var Xa=J=>{var je=hm(),ve=i(je);we(ve,17,()=>r(Ft),ye,(De,sr)=>{var ar=gm(),Or=i(ar);N(()=>S(Or,`${r(sr).label??""} ×`)),$("click",ar,()=>c(_,new Set(r(Pe).filter($r=>$r!==r(sr).name)),!0)),p(De,ar)});var me=f(ve,2);$("click",me,()=>c(_,new Set,!0)),p(J,je)};A(ba,J=>{r(Pe).length>0&&J(Xa)})}var Fa=f(ba,2),Ba=i(Fa),Qa=i(Ba);Bn(Qa,{size:12,class:"pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim"});var _n=f(Qa,2),Za=f(Ba,2);{var Ve=J=>{var je=_m(),ve=i(je);N(()=>S(ve,r(W))),p(J,je)};A(Za,J=>{r(W)&&J(Ve)})}var Ze=f(Za,2);{var Wt=J=>{var je=ym(),ve=i(je);Tr(ve,{size:14,class:"animate-spin"}),p(J,je)},jt=J=>{var je=wm();p(J,je)},Ct=J=>{var je=Me(),ve=te(je);we(ve,17,()=>r(ie),ye,(me,De)=>{var sr=se(()=>lo(r(De),2));let ar=()=>r(sr)[0],Or=()=>r(sr)[1];var $r=Mm(),pr=i($r),dr=i(pr);{var Fr=it=>{jd(it,{size:13,class:"mt-0.5 flex-shrink-0 text-dl-text-dim"})},Qr=se(()=>r(T).has(ar())),Gr=it=>{vi(it,{size:13,class:"mt-0.5 flex-shrink-0 text-dl-text-dim"})};A(dr,it=>{r(Qr)?it(Fr):it(Gr,-1)})}var Zr=f(dr,2),ea=i(Zr),at=i(ea),At=i(at),Yt=f(at,2),xr=i(Yt),Er=f(ea,2),Jt=i(Er),mr=f(pr,2);{var Ir=it=>{var Zt=Em();we(Zt,21,Or,ye,(Lt,ee)=>{var Re=Sm(),We=i(Re);{var Dt=Nt=>{var Xt=km();N(Va=>{Ge(Xt,1,Va),ka(Xt,"aria-label",`${r(ee).label} 선택`)},[()=>ut(vt("flex h-4 w-4 items-center justify-center rounded border flex-shrink-0",r(_).has(r(ee).name)?"border-dl-primary bg-dl-primary/20 text-dl-primary-light":"border-dl-border text-transparent"))]),$("click",Xt,()=>Be(r(ee))),p(Nt,Xt)},nr=Nt=>{var Xt=Cm();p(Nt,Xt)};A(We,Nt=>{r(ee).available?Nt(Dt):Nt(nr,-1)})}var lr=f(We,2),cr=i(lr);{var Ht=Nt=>{xs(Nt,{size:11,class:"flex-shrink-0 text-dl-text-dim"})},or=Nt=>{zn(Nt,{size:11,class:"flex-shrink-0 text-dl-text-dim"})};A(cr,Nt=>{r(ee).dataType==="timeseries"||r(ee).dataType==="table"||r(ee).dataType==="dataframe"?Nt(Ht):Nt(or,-1)})}var br=f(cr,2),ur=i(br),Mr=i(ur),Br=f(ur,2),za=i(Br);N((Nt,Xt)=>{Ge(Re,1,Nt),lr.disabled=!r(ee).available,S(Mr,r(ee).label),S(za,Xt)},[()=>{var Nt;return ut(vt("flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-all",!r(ee).available&&"cursor-default opacity-35",r(ee).available&&((Nt=r(I))==null?void 0:Nt.name)===r(ee).name?"border-dl-primary/40 bg-dl-primary/[0.08]":r(ee).available?"border-transparent bg-white/[0.01] hover:border-dl-primary/20 hover:bg-white/[0.03]":"border-transparent bg-transparent"))},()=>Q(r(ee))]),$("click",lr,()=>Tt({...r(ee),category:ar()})),p(Lt,Re)}),p(it,Zt)},hr=se(()=>r(T).has(ar()));A(mr,it=>{r(hr)&&it(Ir)})}N((it,Zt,Lt)=>{S(At,it),S(xr,Zt),S(Jt,Lt)},[()=>h(ar()),()=>B(Or()),()=>P(ar())]),$("click",pr,()=>bt(ar())),p(me,$r)}),p(J,je)};A(Ze,J=>{r(R)?J(Wt):r(ie).length===0&&r(ht)?J(jt,1):J(Ct,-1)})}var Kt=f(Oe,2),rr=i(Kt);{var tr=J=>{var je=zm(),ve=i(je);xs(ve,{size:28,class:"mx-auto mb-3 text-dl-text-dim/50"}),p(J,je)},dt=J=>{var je=Tm(),ve=i(je);Tr(ve,{size:14,class:"animate-spin"});var me=f(ve);N(()=>S(me,` ${r(I).label??""} 미리보기 로딩 중...`)),p(J,je)},_e=J=>{var je=Wm(),ve=te(je),me=i(ve),De=i(me),sr=i(De),ar=i(sr),Or=f(sr,2),$r=i(Or),pr=f(De,2),dr=i(pr);{var Fr=ee=>{var Re=Am(),We=i(Re);bf(We,{size:11,class:"inline mr-1"});var Dt=f(We);N(nr=>{Ge(Re,1,nr),S(Dt,` ${r(H)?"한글":"EN"}`)},[()=>ut(vt("rounded-lg px-2 py-1 text-[10px] transition-colors",r(H)?"bg-dl-primary/15 text-dl-primary-light":"text-dl-text-dim hover:bg-white/5 hover:text-dl-text"))]),$("click",Re,()=>c(H,!r(H))),p(ee,Re)},Qr=se(()=>Et());A(dr,ee=>{r(Qr)&&ee(Fr)})}var Gr=f(dr,2),Zr=i(Gr);jn(Zr,{size:11,class:"inline mr-1"});var ea=f(me,2);we(ea,21,()=>r(Vt),ye,(ee,Re)=>{var We=Nm(),Dt=i(We);N(()=>S(Dt,r(Re))),p(ee,We)});var at=f(ea,2),At=f(i(at),2),Yt=i(At),xr=f(At,2),Er=f(ve,2);{var Jt=ee=>{var Re=Pm(),We=i(Re),Dt=i(We),nr=i(Dt),lr=f(i(nr));we(lr,17,Je,ye,(Ht,or)=>{var br=Om(),ur=i(br);N(()=>S(ur,r(or))),p(Ht,br)});var cr=f(Dt);we(cr,21,()=>r(y).rows,ye,(Ht,or)=>{const br=se(()=>r(or).계정명),ur=se(()=>le(r(br)));var Mr=Lm(),Br=i(Mr),za=i(Br),Nt=f(Br);we(Nt,17,Je,ye,(Xt,Va)=>{const en=se(()=>r(or)[r(Va)]);var gl=Im(),Ro=i(gl);N((tn,hl)=>{Ge(gl,1,tn),S(Ro,hl)},[()=>ut(vt("border-b border-dl-border/10 px-3 py-1.5 text-right font-mono text-[10px]",r(en)===null||r(en)===void 0?"text-dl-text-dim/30":typeof r(en)=="number"&&r(en)<0?"text-dl-primary-light":"text-dl-accent-light")),()=>Se(r(en),ct())]),p(Xt,gl)}),N((Xt,Va)=>{Ge(Br,1,Xt),so(Br,`padding-left: ${8+(r(ur)-1)*12}px`),S(za,Va)},[()=>ut(vt("sticky left-0 border-b border-r border-dl-border/10 bg-dl-bg-card/95 px-3 py-1.5 whitespace-nowrap",r(ur)===1&&"font-semibold text-dl-text",r(ur)===2&&"text-dl-text-muted",r(ur)>=3&&"text-dl-text-dim")),()=>xe(r(br))]),p(Ht,Mr)}),p(ee,Re)},mr=se(()=>r(y).type==="table"&&Et()),Ir=ee=>{var Re=qm(),We=i(Re),Dt=i(We),nr=i(Dt);we(nr,21,()=>r(y).columns,ye,(cr,Ht)=>{var or=Rm(),br=i(or);N(()=>S(br,r(Ht))),p(cr,or)});var lr=f(Dt);we(lr,21,()=>r(y).rows,ye,(cr,Ht)=>{var or=Dm();we(or,21,()=>r(y).columns,ye,(br,ur)=>{const Mr=se(()=>r(Ht)[r(ur)]);var Br=jm(),za=i(Br);N((Nt,Xt)=>{Ge(Br,1,Nt),S(za,Xt)},[()=>ut(vt("border-b border-dl-border/10 px-3 py-1.5 whitespace-nowrap",typeof r(Mr)=="number"?"text-right font-mono text-[10px] text-dl-accent-light":"text-dl-text-muted")),()=>Se(r(Mr),ct())]),p(br,Br)}),p(cr,or)}),p(ee,Re)},hr=ee=>{var Re=Fm();we(Re,21,()=>Object.entries(r(y).data||{}),ye,(We,Dt)=>{var nr=se(()=>lo(r(Dt),2));let lr=()=>r(nr)[0],cr=()=>r(nr)[1];var Ht=$m(),or=i(Ht),br=i(or),ur=f(or,2),Mr=i(ur);N(()=>{S(br,lr()),S(Mr,cr()??"-")}),p(We,Ht)}),p(ee,Re)},it=ee=>{var Re=Gm(),We=i(Re);{var Dt=cr=>{var Ht=Vm(),or=f(i(Ht),2);we(or,21,()=>r(ir),ye,(br,ur)=>{var Mr=Bm(),Br=i(Mr);N(()=>S(Br,r(ur))),p(br,Mr)}),p(cr,Ht)};A(We,cr=>{r(ir).length>0&&cr(Dt)})}var nr=f(We,2),lr=i(nr);N(()=>S(lr,r(y).text)),p(ee,Re)},Zt=ee=>{var Re=Hm(),We=i(Re);N(()=>S(We,r(y).error||"데이터를 불러올 수 없습니다.")),p(ee,Re)},Lt=ee=>{var Re=Um(),We=i(Re),Dt=i(We);N(nr=>S(Dt,nr),[()=>r(y).data||JSON.stringify(r(y),null,2)]),p(ee,Re)};A(Er,ee=>{r(mr)?ee(Jt):r(y).type==="table"?ee(Ir,1):r(y).type==="dict"?ee(hr,2):r(y).type==="text"?ee(it,3):r(y).type==="error"?ee(Zt,4):ee(Lt,-1)})}N((ee,Re)=>{S(ar,r(I).label),S($r,ee),S(Yt,Re)},[()=>Q(r(I)),()=>pe(r(I))]),$("click",Gr,()=>$e([r(I).name])),$("click",xr,Te),p(J,je)};A(rr,J=>{r(I)?r(M)?J(dt,1):r(y)&&J(_e,2):J(tr)})}N(()=>{S(qe,`${r(ne)??""}개 모듈`),S(yr,r(Pe).length>0?`${r(Pe).length}개 모듈 선택됨`:"다운로드할 모듈을 선택하거나 전체 Excel을 받으세요."),ke.disabled=r(F)||r(Pe).length===0,Ur.disabled=r(Pe).length===0,la.disabled=r(F)}),$("click",ke,()=>$e(r(Pe))),$("click",Ur,()=>c(_,new Set,!0)),$("click",la,()=>$e()),Pn(_n,()=>r(he),J=>c(he,J)),p(G,ce)};A(z,G=>{a()?G(q,-1):G(j)})}p(u,b)};A(Oo,u=>{l()==="sections"?u(Yl):l()==="overview"?u(Io,1):l()==="evidence"?u(Lo,2):u(Po,-1)})}var w=f(hn,2);{var V=u=>{var b=Zm(),z=i(b),j=i(z),q=i(j),G=i(q),ce=i(G),Oe=f(G,2),_t=i(Oe),K=f(q,2),oe=i(K);Xn(oe,{size:16});var qe=f(j,2),fr=i(qe);{var Rt=ke=>{var Qt=Ym(),Gt=i(Qt),Ut=i(Gt);N(()=>{var Ur;return S(Ut,((Ur=r(ge).payload)==null?void 0:Ur.text)||"-")}),p(ke,Qt)},er=ke=>{var Qt=Jm(),Gt=i(Qt);N(Ut=>S(Gt,Ut),[()=>JSON.stringify(r(ge).payload,null,2)]),p(ke,Qt)},yr=ke=>{var Qt=Xm(),Gt=i(Qt);N(Ut=>S(Gt,Ut),[()=>JSON.stringify(r(ge).payload,null,2)]),p(ke,Qt)},It=ke=>{var Qt=Qm(),Gt=i(Qt),Ut=i(Gt);N(()=>S(Ut,r(ge).payload||"-")),p(ke,Qt)};A(fr,ke=>{r(ge).type==="context"?ke(Rt):r(ge).type==="tool"||r(ge).type==="tool-call"||r(ge).type==="tool-result"?ke(er,1):r(ge).type==="snapshot"?ke(yr,2):ke(It,-1)})}pn(z,ke=>c(wt,ke),()=>r(wt)),N(()=>{S(ce,r(ge).title),S(_t,r(ge).type==="context"?"Context Detail":r(ge).type==="tool"||r(ge).type==="tool-call"||r(ge).type==="tool-result"?"Tool Event":r(ge).type==="snapshot"?"Snapshot":"Prompt Detail")}),$("click",b,ke=>{ke.target===ke.currentTarget&&Pt()}),$("keydown",z,ke=>{ke.key==="Escape"&&Pt()}),$("click",K,Pt),p(u,b)};A(w,u=>{r(ge)&&u(V)})}N((u,b,z,j)=>{Ge(Kn,1,u),Ge(ml,1,b),Ge(bl,1,z),Ge(Hl,1,j)},[()=>ut(vt("rounded-lg px-2 py-1.5 text-[11px] transition-colors",l()==="sections"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted")),()=>ut(vt("rounded-lg px-2 py-1.5 text-[11px] transition-colors",l()==="overview"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted")),()=>ut(vt("rounded-lg px-2 py-1.5 text-[11px] transition-colors",l()==="explore"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted")),()=>ut(vt("rounded-lg px-2 py-1.5 text-[11px] transition-colors",l()==="evidence"?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted"))]),$("input",Wn,Ot),Pn(Wn,()=>r(v),u=>c(v,u)),$("click",Kn,()=>Z("sections")),$("click",ml,()=>Z("overview")),$("click",bl,()=>Z("explore")),$("click",Hl,()=>Z("evidence")),p(e,xa),pa()}Ya(["click","input","keydown"]);var tb=m('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),rb=m("<!> <span>확인 중...</span>",1),ab=m("<!> <span>설정 필요</span>",1),nb=m('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),lb=m('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!> <!>',1),ob=m('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/80 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text-muted">AI Provider 확인 중...</div></div></div>'),ib=m('<div class="mx-3 mb-2 px-4 py-3 rounded-xl border border-dl-primary/30 bg-dl-primary/5 backdrop-blur-sm flex items-center gap-3 pointer-events-auto"><!> <div class="flex-1"><div class="text-[13px] text-dl-text">AI Provider가 설정되지 않았습니다</div> <div class="text-[11px] text-dl-text-muted mt-0.5">대화를 시작하려면 Provider를 설정해주세요</div></div> <button class="px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors flex-shrink-0">설정하기</button></div>'),sb=m('<div class="surface-panel w-[400px] flex-shrink-0 border-l border-dl-border/60 bg-dl-bg-card/35 pt-11"><!></div>'),db=m('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),cb=m('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),ub=m('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),vb=m('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),fb=m('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),pb=m('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),xb=m('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),mb=m('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),bb=m('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),gb=m('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),hb=m('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),_b=m('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @anthropic-ai/claude-code</div></div></div>'),yb=m('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">인증</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">claude auth login</div></div></div></div> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">Claude Pro 또는 Max 구독이 필요합니다</span></div>',1),wb=m('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2">설치 완료 후 새로고침하세요</div></div>'),kb=m("<!> 브라우저에서 로그인 중...",1),Cb=m("<!> OpenAI 계정으로 로그인",1),Sb=m('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2.5">ChatGPT 계정으로 로그인하여 사용하세요</div> <button class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div></div>'),Eb=m('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Mb=m('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),zb=m("<button> <!></button>"),Tb=m('<div class="flex flex-wrap gap-1.5"></div>'),Ab=m('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Nb=m('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Ob=m('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Ib=m('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Lb=m('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Pb=m('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Rb=m('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),jb=m("<!> <!> <!> <!> <!> <!> <!>",1),Db=m('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),qb=m('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),$b=m('<div class="fixed inset-0 z-[190] bg-black/50 backdrop-blur-sm" role="presentation"><div class="mobile-workspace-sheet absolute inset-x-0 bottom-0 top-[12vh] rounded-t-[24px] border border-dl-border bg-dl-bg-card shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="mobile-workspace-title" tabindex="-1"><div class="flex items-center justify-between px-4 pt-2 pb-1"><div class="flex-1 flex justify-center"><div class="h-1.5 w-14 rounded-full bg-dl-border/80"></div></div> <button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="워크스페이스 닫기"><!></button></div> <div id="mobile-workspace-title" class="px-4 pb-2 text-[11px] uppercase tracking-[0.16em] text-dl-text-dim">Workspace</div> <!></div></div>'),Fb=m('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Bb=m('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Vb=m('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-0 left-0 right-0 z-10 pointer-events-none"><div class="flex items-center justify-between px-3 h-11 pointer-events-auto" style="background: linear-gradient(to bottom, rgba(5,8,17,0.92) 40%, transparent);"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button> <div class="flex items-center gap-1"><button><!> <span> </span></button> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <div class="w-px h-4 bg-dl-border mx-1"></div> <button aria-label="AI Provider 설정 열기"><!> <!></button></div></div> <!></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function Gb(e,t){fa(t,!0);let a=D(""),n=D(!1),l=D(null),o=D(yt({})),s=D(yt({})),d=D(null),v=D(null),x=D(yt([])),g=D(!0),k=D(0),C=D(!0),R=D(""),T=D(!1),I=D(null),y=D(yt({})),M=D(yt({})),F=D(""),H=D(!1),_=D(null),L=D(""),U=D(!1),re=D(""),E=D(0),Y=D(null),X=D(!1),Ce=D(yt({})),lt=D(null),he=D(null),fe=D(null);const W=rf();let Ae=D(!1);function ot(){c(Ae,window.innerWidth<=768),r(Ae)?(c(g,!1),W.close()):W.userPinnedCompany||W.open("overview")}na(()=>(ot(),window.addEventListener("resize",ot),()=>window.removeEventListener("resize",ot))),na(()=>{!r(T)||!r(lt)||requestAnimationFrame(()=>{var w;return(w=r(lt))==null?void 0:w.focus()})}),na(()=>{!r(ge)||!r(he)||requestAnimationFrame(()=>{var w;return(w=r(he))==null?void 0:w.focus()})}),na(()=>{!r(Ae)||!W.isOpen||!r(fe)||requestAnimationFrame(()=>{var w;return(w=r(fe))==null?void 0:w.focus()})});let ge=D(null),wt=D(""),ae=D("error"),qt=D(!1);function Ne(w,V="error",u=4e3){c(wt,w,!0),c(ae,V,!0),c(qt,!0),setTimeout(()=>{c(qt,!1)},u)}const h=Yv();na(()=>{Q()});let P=D(yt({})),B=D(yt({}));async function Q(){var w,V,u;c(C,!0);try{const b=await Gu();c(o,b.providers||{},!0),c(s,b.ollama||{},!0),c(P,b.codex||{},!0),c(B,b.claudeCode||{},!0),c(Ce,b.chatgpt||{},!0),b.version&&c(R,b.version,!0);const z=localStorage.getItem("dartlab-provider"),j=localStorage.getItem("dartlab-model");if(z&&((w=r(o)[z])!=null&&w.available)){c(d,z,!0),c(I,z,!0),await Yn(z,j),await pe(z);const q=r(y)[z]||[];j&&q.includes(j)?c(v,j,!0):q.length>0&&(c(v,q[0],!0),localStorage.setItem("dartlab-model",r(v))),c(x,q,!0),c(C,!1);return}if(z&&r(o)[z]){c(d,z,!0),c(I,z,!0),await pe(z);const q=r(y)[z]||[];c(x,q,!0),j&&q.includes(j)?c(v,j,!0):q.length>0&&c(v,q[0],!0),c(C,!1);return}for(const q of["chatgpt","codex","ollama"])if((V=r(o)[q])!=null&&V.available){c(d,q,!0),c(I,q,!0),await Yn(q),await pe(q);const G=r(y)[q]||[];c(x,G,!0),c(v,((u=r(o)[q])==null?void 0:u.model)||(G.length>0?G[0]:null),!0),r(v)&&localStorage.setItem("dartlab-model",r(v));break}}catch{}c(C,!1)}async function pe(w){c(M,{...r(M),[w]:!0},!0);try{const V=await Hu(w);c(y,{...r(y),[w]:V.models||[]},!0)}catch{c(y,{...r(y),[w]:[]},!0)}c(M,{...r(M),[w]:!1},!0)}async function xe(w){var u;c(d,w,!0),c(v,null),c(I,w,!0),localStorage.setItem("dartlab-provider",w),localStorage.removeItem("dartlab-model"),c(F,""),c(_,null);try{await Yn(w)}catch{}await pe(w);const V=r(y)[w]||[];if(c(x,V,!0),V.length>0){c(v,((u=r(o)[w])==null?void 0:u.model)||V[0],!0),localStorage.setItem("dartlab-model",r(v));try{await Yn(w,r(v))}catch{}}}async function le(w){c(v,w,!0),localStorage.setItem("dartlab-model",w);try{await Yn(r(d),w)}catch{}}function ct(w){r(I)===w?c(I,null):(c(I,w,!0),pe(w))}async function Et(){const w=r(F).trim();if(!(!w||!r(d))){c(H,!0),c(_,null);try{const V=await Yn(r(d),r(v),w);V.available?(c(_,"success"),r(o)[r(d)]={...r(o)[r(d)],available:!0,model:V.model},!r(v)&&V.model&&c(v,V.model,!0),await pe(r(d)),c(x,r(y)[r(d)]||[],!0),Ne("API 키 인증 성공","success")):c(_,"error")}catch{c(_,"error")}c(H,!1)}}async function Je(){if(!r(X)){c(X,!0);try{const{authUrl:w}=await Wu();window.open(w,"dartlab-oauth","width=600,height=700");const V=setInterval(async()=>{var u;try{const b=await Ku();b.done&&(clearInterval(V),c(X,!1),b.error?Ne(`인증 실패: ${b.error}`):(Ne("ChatGPT 인증 성공","success"),await Q(),(u=r(o).chatgpt)!=null&&u.available&&await xe("chatgpt")))}catch{clearInterval(V),c(X,!1)}},2e3);setTimeout(()=>{clearInterval(V),r(X)&&(c(X,!1),Ne("인증 시간이 초과되었습니다. 다시 시도해주세요."))},12e4)}catch(w){c(X,!1),Ne(`OAuth 시작 실패: ${w.message}`)}}}async function ze(){try{await Yu(),c(Ce,{authenticated:!1},!0),r(d)==="chatgpt"&&c(o,{...r(o),chatgpt:{...r(o).chatgpt,available:!1}},!0),Ne("ChatGPT 로그아웃 완료","success"),await Q()}catch{Ne("로그아웃 실패")}}function Mt(){const w=r(L).trim();!w||r(U)||(c(U,!0),c(re,"준비 중..."),c(E,0),c(Y,Uu(w,{onProgress(V){V.total&&V.completed!==void 0?(c(E,Math.round(V.completed/V.total*100),!0),c(re,`다운로드 중... ${r(E)}%`)):V.status&&c(re,V.status,!0)},async onDone(){c(U,!1),c(Y,null),c(L,""),c(re,""),c(E,0),Ne(`${w} 다운로드 완료`,"success"),await pe("ollama"),c(x,r(y).ollama||[],!0),r(x).includes(w)&&await le(w)},onError(V){c(U,!1),c(Y,null),c(re,""),c(E,0),Ne(`다운로드 실패: ${V}`)}}),!0))}function Se(){r(Y)&&(r(Y).abort(),c(Y,null)),c(U,!1),c(L,""),c(re,""),c(E,0)}function Ie(){c(g,!r(g))}function Le(w="explore"){W.open(w)}function zt(){W.close()}function Ot(w,V){if(!w||!V)return;const u=w.corpName||w.company||w.stockCode;c(a,`${u}의 ${V.label} 데이터를 바탕으로 핵심 포인트를 요약해줘`),W.selectCompany(w,{pin:!0}),Le("evidence")}function mt(w,V=null){W.openEvidence(w,V)}function Fe(){if(c(F,""),c(_,null),r(d))c(I,r(d),!0);else{const w=Object.keys(r(o));c(I,w.length>0?w[0]:null,!0)}c(T,!0),r(I)&&pe(r(I))}function bt(w){var V,u,b,z;if(w)for(let j=w.messages.length-1;j>=0;j--){const q=w.messages[j];if(q.role==="assistant"&&((V=q.meta)!=null&&V.stockCode||(u=q.meta)!=null&&u.company||q.company)){W.syncCompanyFromMessage({company:((b=q.meta)==null?void 0:b.company)||q.company,stockCode:(z=q.meta)==null?void 0:z.stockCode},W.selectedCompany);return}}}function Tt(){h.createConversation(),W.clearEvidenceSelection(),c(a,""),c(n,!1),r(l)&&(r(l).abort(),c(l,null))}function $e(w){h.setActive(w),W.clearEvidenceSelection(),bt(h.active),c(a,""),c(n,!1),r(l)&&(r(l).abort(),c(l,null))}function Be(w){c(ge,w,!0)}function Te(){r(ge)&&(h.deleteConversation(r(ge)),c(ge,null))}function rt(){var V;const w=h.active;if(!w)return null;for(let u=w.messages.length-1;u>=0;u--){const b=w.messages[u];if(b.role==="assistant"&&((V=b.meta)!=null&&V.stockCode))return b.meta.stockCode}return null}async function ie(){var ce,Oe,_t;const w=r(a).trim();if(!w||r(n))return;if(!r(d)||!((ce=r(o)[r(d)])!=null&&ce.available)){Ne("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),Fe();return}h.activeId||h.createConversation();const V=h.activeId;h.addMessage("user",w),c(a,""),c(n,!0),h.addMessage("assistant",""),h.updateLastMessage({loading:!0,startedAt:Date.now()}),Ml(k);const u=h.active,b=[];let z=null;if(u){const K=u.messages.slice(0,-2);for(const oe of K)if((oe.role==="user"||oe.role==="assistant")&&oe.text&&oe.text.trim()&&!oe.error&&!oe.loading){const qe={role:oe.role,text:oe.text};oe.role==="assistant"&&((Oe=oe.meta)!=null&&Oe.stockCode)&&(qe.meta={company:oe.meta.company||oe.company,stockCode:oe.meta.stockCode,modules:oe.meta.includedModules||null},z=oe.meta.stockCode),b.push(qe)}}const j=((_t=W.selectedCompany)==null?void 0:_t.stockCode)||z||rt();function q(){return h.activeId!==V}const G=rv(j,w,{provider:r(d),model:r(v)},{onMeta(K){var er;if(q())return;const oe=h.active,qe=oe==null?void 0:oe.messages[oe.messages.length-1],Rt={meta:{...(qe==null?void 0:qe.meta)||{},...K}};K.company&&(Rt.company=K.company,h.activeId&&((er=h.active)==null?void 0:er.title)==="새 대화"&&h.updateTitle(h.activeId,K.company)),K.stockCode&&(Rt.stockCode=K.stockCode),(K.company||K.stockCode)&&W.syncCompanyFromMessage(K,W.selectedCompany),h.updateLastMessage(Rt)},onSnapshot(K){q()||h.updateLastMessage({snapshot:K})},onContext(K){if(q())return;const oe=h.active;if(!oe)return;const qe=oe.messages[oe.messages.length-1],fr=(qe==null?void 0:qe.contexts)||[];h.updateLastMessage({contexts:[...fr,{module:K.module,label:K.label,text:K.text}]})},onSystemPrompt(K){q()||h.updateLastMessage({systemPrompt:K.text,userContent:K.userContent||null})},onToolCall(K){if(q())return;const oe=h.active;if(!oe)return;const qe=oe.messages[oe.messages.length-1],fr=(qe==null?void 0:qe.toolEvents)||[];h.updateLastMessage({toolEvents:[...fr,{type:"call",name:K.name,arguments:K.arguments}]})},onToolResult(K){if(q())return;const oe=h.active;if(!oe)return;const qe=oe.messages[oe.messages.length-1],fr=(qe==null?void 0:qe.toolEvents)||[];h.updateLastMessage({toolEvents:[...fr,{type:"result",name:K.name,result:K.result}]})},onChunk(K){if(q())return;const oe=h.active;if(!oe)return;const qe=oe.messages[oe.messages.length-1];h.updateLastMessage({text:((qe==null?void 0:qe.text)||"")+K}),Ml(k)},onDone(){if(q())return;const K=h.active,oe=K==null?void 0:K.messages[K.messages.length-1],qe=oe!=null&&oe.startedAt?((Date.now()-oe.startedAt)/1e3).toFixed(1):null;h.updateLastMessage({loading:!1,duration:qe}),h.flush(),c(n,!1),c(l,null),Ml(k)},onError(K,oe,qe){q()||(h.updateLastMessage({text:`오류: ${K}`,loading:!1,error:!0}),h.flush(),oe==="relogin"||oe==="login"?(Ne(`${K} — 설정에서 재로그인하세요`),Fe()):Ne(oe==="check_headers"||oe==="check_endpoint"||oe==="check_client_id"?`${K} — ChatGPT API 변경 감지. 업데이트를 확인하세요`:oe==="rate_limit"?"요청이 너무 많습니다. 잠시 후 다시 시도해주세요":K),c(n,!1),c(l,null))}},b);c(l,G,!0)}function ne(){r(l)&&(r(l).abort(),c(l,null),c(n,!1),h.updateLastMessage({loading:!1}),h.flush())}function be(){const w=h.active;if(!w||w.messages.length<2)return;let V="";for(let u=w.messages.length-1;u>=0;u--)if(w.messages[u].role==="user"){V=w.messages[u].text;break}V&&(h.removeLastMessage(),h.removeLastMessage(),c(a,V,!0),requestAnimationFrame(()=>{ie()}))}function Ee(){const w=h.active;if(!w)return;let V=`# ${w.title}

`;for(const j of w.messages)j.role==="user"?V+=`## You

${j.text}

`:j.role==="assistant"&&j.text&&(V+=`## DartLab

${j.text}

`);const u=new Blob([V],{type:"text/markdown;charset=utf-8"}),b=URL.createObjectURL(u),z=document.createElement("a");z.href=b,z.download=`${w.title||"dartlab-chat"}.md`,z.click(),URL.revokeObjectURL(b),Ne("대화가 마크다운으로 내보내졌습니다","success")}function Xe(w){(w.metaKey||w.ctrlKey)&&w.key==="n"&&(w.preventDefault(),Tt()),(w.metaKey||w.ctrlKey)&&w.shiftKey&&w.key==="S"&&(w.preventDefault(),Ie()),w.key==="Escape"&&r(T)?c(T,!1):w.key==="Escape"&&r(ge)?c(ge,null):w.key==="Escape"&&W.isOpen&&W.close()}let Qe=se(()=>{var w;return((w=h.active)==null?void 0:w.messages)||[]}),gt=se(()=>h.active&&h.active.messages.length>0),$t=se(()=>{var w;return!r(C)&&(!r(d)||!((w=r(o)[r(d)])!=null&&w.available))}),Vt=se(()=>{for(let w=r(Qe).length-1;w>=0;w--)if(r(Qe)[w].role==="assistant")return r(Qe)[w];return null});const ir=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var ht=Vb();io("keydown",ni,Xe);var Pe=te(ht),Ft=i(Pe);{var Z=w=>{var V=tb();$("click",V,()=>{c(g,!1)}),p(w,V)};A(Ft,w=>{r(Ae)&&r(g)&&w(Z)})}var Ue=f(Ft,2),Pt=i(Ue);{let w=se(()=>r(Ae)?!0:r(g));Ff(Pt,{get conversations(){return h.conversations},get activeId(){return h.activeId},get open(){return r(w)},get version(){return r(R)},onNewChat:()=>{Tt(),r(Ae)&&c(g,!1)},onSelect:V=>{$e(V),r(Ae)&&c(g,!1)},onDelete:Be})}var kt=f(Ue,2),Bt=i(kt),_r=i(Bt),vr=i(_r),Nr=i(vr);{var Vr=w=>{wf(w,{size:18})},qa=w=>{yf(w,{size:18})};A(Nr,w=>{r(g)?w(Vr):w(qa,-1)})}var Ma=f(vr,2),xa=i(Ma),hn=i(xa);Cr(hn,{size:12});var Hn=f(hn,2),Dl=i(Hn),xl=f(xa,2),ko=i(xl);xf(ko,{size:15});var ql=f(xl,2),Co=i(ql);zn(Co,{size:15});var $l=f(ql,2),Fl=i($l);mf(Fl,{size:15});var Un=f($l,4),Wn=i(Un);{var So=w=>{var V=rb(),u=te(V);Tr(u,{size:12,class:"animate-spin"}),p(w,V)},Eo=w=>{var V=ab(),u=te(V);wn(u,{size:12}),p(w,V)},Bl=w=>{var V=lb(),u=f(te(V),2),b=i(u),z=f(u,2);{var j=ce=>{var Oe=nb(),_t=f(te(Oe),2),K=i(_t);N(()=>S(K,r(v))),p(ce,Oe)};A(z,ce=>{r(v)&&ce(j)})}var q=f(z,2);{var G=ce=>{Tr(ce,{size:10,class:"animate-spin text-dl-primary-light"})};A(q,ce=>{r(U)&&ce(G)})}N(()=>S(b,r(d))),p(w,V)};A(Wn,w=>{r(C)?w(So):r($t)?w(Eo,1):w(Bl,-1)})}var Mo=f(Wn,2);Ef(Mo,{size:12});var Vl=f(_r,2);{var zo=w=>{var V=ob(),u=i(V);Tr(u,{size:16,class:"text-dl-text-dim animate-spin flex-shrink-0"}),p(w,V)},To=w=>{var V=ib(),u=i(V);wn(u,{size:16,class:"text-dl-primary-light flex-shrink-0"});var b=f(u,4);$("click",b,()=>Fe()),p(w,V)};A(Vl,w=>{r(C)&&!r(T)?w(zo):r($t)&&!r(T)&&w(To,1)})}var Gl=f(Bt,2),Kn=i(Gl),ml=i(Kn);{var bl=w=>{Up(w,{get messages(){return r(Qe)},get isLoading(){return r(n)},get scrollTrigger(){return r(k)},get selectedCompany(){return W.selectedCompany},onSend:ie,onStop:ne,onRegenerate:be,onExport:Ee,onOpenExplorer:Le,onOpenEvidence:mt,get inputText(){return r(a)},set inputText(V){c(a,V,!0)}})},Hl=w=>{Xf(w,{get selectedCompany(){return W.selectedCompany},onSend:ie,onOpenExplorer:Le,get inputText(){return r(a)},set inputText(V){c(a,V,!0)}})};A(ml,w=>{r(gt)?w(bl):w(Hl,-1)})}var Ao=f(Kn,2);{var No=w=>{var V=sb(),u=i(V);bs(u,{get selectedCompany(){return W.selectedCompany},get recentCompanies(){return W.recentCompanies},get activeTab(){return W.activeTab},get evidenceMessage(){return r(Vt)},get activeEvidenceSection(){return W.activeEvidenceSection},get selectedEvidenceIndex(){return W.selectedEvidenceIndex},onSelectCompany:b=>W.selectCompany(b,{pin:!0}),onChangeTab:b=>W.setTab(b),onAskAboutModule:Ot,onNotify:Ne,onClose:zt}),p(w,V)};A(Ao,w=>{!r(Ae)&&W.isOpen&&w(No)})}var Ul=f(Pe,2);{var Wl=w=>{var V=qb(),u=i(V),b=i(u),z=i(b),j=f(i(z),2),q=i(j);Xn(q,{size:18});var G=f(b,2),ce=i(G);we(ce,21,()=>Object.entries(r(o)),ye,(Rt,er)=>{var yr=se(()=>lo(r(er),2));let It=()=>r(yr)[0],ke=()=>r(yr)[1];const Qt=se(()=>It()===r(d)),Gt=se(()=>r(I)===It()),Ut=se(()=>ke().auth==="api_key"),Ur=se(()=>ke().auth==="cli"),la=se(()=>r(y)[It()]||[]),Ja=se(()=>r(M)[It()]);var $a=Db(),ma=i($a),ba=i(ma),Xa=f(ba,2),Fa=i(Xa),Ba=i(Fa),Qa=i(Ba),_n=f(Ba,2);{var Za=_e=>{var J=db();p(_e,J)};A(_n,_e=>{r(Qt)&&_e(Za)})}var Ve=f(Fa,2),Ze=i(Ve),Wt=f(Xa,2),jt=i(Wt);{var Ct=_e=>{Rn(_e,{size:16,class:"text-dl-success"})},Kt=_e=>{var J=cb(),je=te(J);vs(je,{size:14,class:"text-amber-400"}),p(_e,J)},rr=_e=>{var J=ub(),je=te(J);Tf(je,{size:14,class:"text-dl-text-dim"}),p(_e,J)};A(jt,_e=>{ke().available?_e(Ct):r(Ut)?_e(Kt,1):r(Ur)&&!ke().available&&_e(rr,2)})}var tr=f(ma,2);{var dt=_e=>{var J=jb(),je=te(J);{var ve=at=>{var At=fb(),Yt=i(At),xr=i(Yt),Er=f(Yt,2),Jt=i(Er),mr=f(Jt,2),Ir=i(mr);{var hr=ee=>{Tr(ee,{size:12,class:"animate-spin"})},it=ee=>{vs(ee,{size:12})};A(Ir,ee=>{r(H)?ee(hr):ee(it,-1)})}var Zt=f(Er,2);{var Lt=ee=>{var Re=vb(),We=i(Re);wn(We,{size:12}),p(ee,Re)};A(Zt,ee=>{r(_)==="error"&&ee(Lt)})}N(ee=>{S(xr,ke().envKey?`환경변수 ${ke().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),ka(Jt,"placeholder",It()==="openai"?"sk-...":It()==="claude"?"sk-ant-...":"API Key"),mr.disabled=ee},[()=>!r(F).trim()||r(H)]),$("keydown",Jt,ee=>{ee.key==="Enter"&&Et()}),Pn(Jt,()=>r(F),ee=>c(F,ee)),$("click",mr,Et),p(at,At)};A(je,at=>{r(Ut)&&!ke().available&&at(ve)})}var me=f(je,2);{var De=at=>{var At=xb(),Yt=i(At),xr=i(Yt);Rn(xr,{size:13,class:"text-dl-success"});var Er=f(Yt,2),Jt=i(Er),mr=f(Jt,2);{var Ir=it=>{var Zt=pb(),Lt=i(Zt);{var ee=We=>{Tr(We,{size:10,class:"animate-spin"})},Re=We=>{var Dt=sa("변경");p(We,Dt)};A(Lt,We=>{r(H)?We(ee):We(Re,-1)})}N(()=>Zt.disabled=r(H)),$("click",Zt,Et),p(it,Zt)},hr=se(()=>r(F).trim());A(mr,it=>{r(hr)&&it(Ir)})}$("keydown",Jt,it=>{it.key==="Enter"&&Et()}),Pn(Jt,()=>r(F),it=>c(F,it)),p(at,At)};A(me,at=>{r(Ut)&&ke().available&&at(De)})}var sr=f(me,2);{var ar=at=>{var At=mb(),Yt=f(i(At),2),xr=i(Yt);jn(xr,{size:14});var Er=f(xr,2);us(Er,{size:10,class:"ml-auto"}),p(at,At)},Or=at=>{var At=bb(),Yt=i(At),xr=i(Yt);wn(xr,{size:14}),p(at,At)};A(sr,at=>{It()==="ollama"&&!r(s).installed?at(ar):It()==="ollama"&&r(s).installed&&!r(s).running&&at(Or,1)})}var $r=f(sr,2);{var pr=at=>{var At=wb(),Yt=i(At);{var xr=Jt=>{var mr=hb(),Ir=te(mr),hr=i(Ir),it=f(Ir,2),Zt=i(it);{var Lt=lr=>{var cr=gb();p(lr,cr)};A(Zt,lr=>{r(P).installed||lr(Lt)})}var ee=f(Zt,2),Re=i(ee),We=i(Re),Dt=f(it,2),nr=i(Dt);wn(nr,{size:12,class:"text-amber-400 flex-shrink-0"}),N(()=>{S(hr,r(P).installed?"Codex CLI가 설치되었지만 인증이 필요합니다":"Codex CLI 설치가 필요합니다"),S(We,r(P).installed?"1.":"2.")}),p(Jt,mr)},Er=Jt=>{var mr=yb(),Ir=te(mr),hr=i(Ir),it=f(Ir,2),Zt=i(it);{var Lt=lr=>{var cr=_b();p(lr,cr)};A(Zt,lr=>{r(B).installed||lr(Lt)})}var ee=f(Zt,2),Re=i(ee),We=i(Re),Dt=f(it,2),nr=i(Dt);wn(nr,{size:12,class:"text-amber-400 flex-shrink-0"}),N(()=>{S(hr,r(B).installed&&!r(B).authenticated?"Claude Code가 설치되었지만 인증이 필요합니다":"Claude Code CLI 설치가 필요합니다"),S(We,r(B).installed?"1.":"2.")}),p(Jt,mr)};A(Yt,Jt=>{It()==="codex"?Jt(xr):It()==="claude-code"&&Jt(Er,1)})}p(at,At)};A($r,at=>{r(Ur)&&!ke().available&&at(pr)})}var dr=f($r,2);{var Fr=at=>{var At=Sb(),Yt=f(i(At),2),xr=i(Yt);{var Er=hr=>{var it=kb(),Zt=te(it);Tr(Zt,{size:14,class:"animate-spin"}),p(hr,it)},Jt=hr=>{var it=Cb(),Zt=te(it);hf(Zt,{size:14}),p(hr,it)};A(xr,hr=>{r(X)?hr(Er):hr(Jt,-1)})}var mr=f(Yt,2),Ir=i(mr);wn(Ir,{size:12,class:"text-amber-400 flex-shrink-0"}),N(()=>Yt.disabled=r(X)),$("click",Yt,Je),p(at,At)};A(dr,at=>{ke().auth==="oauth"&&!ke().available&&at(Fr)})}var Qr=f(dr,2);{var Gr=at=>{var At=Eb(),Yt=i(At),xr=i(Yt),Er=i(xr);Rn(Er,{size:13,class:"text-dl-success"});var Jt=f(xr,2),mr=i(Jt);_f(mr,{size:11}),$("click",Jt,ze),p(at,At)};A(Qr,at=>{ke().auth==="oauth"&&ke().available&&at(Gr)})}var Zr=f(Qr,2);{var ea=at=>{var At=Rb(),Yt=i(At),xr=f(i(Yt),2);{var Er=Lt=>{Tr(Lt,{size:12,class:"animate-spin text-dl-text-dim"})};A(xr,Lt=>{r(Ja)&&Lt(Er)})}var Jt=f(Yt,2);{var mr=Lt=>{var ee=Mb(),Re=i(ee);Tr(Re,{size:14,class:"animate-spin"}),p(Lt,ee)},Ir=Lt=>{var ee=Tb();we(ee,21,()=>r(la),ye,(Re,We)=>{var Dt=zb(),nr=i(Dt),lr=f(nr);{var cr=Ht=>{vf(Ht,{size:10,class:"inline ml-1"})};A(lr,Ht=>{r(We)===r(v)&&r(Qt)&&Ht(cr)})}N(Ht=>{Ge(Dt,1,Ht),S(nr,`${r(We)??""} `)},[()=>ut(vt("px-3 py-1.5 rounded-lg text-[11px] border transition-all",r(We)===r(v)&&r(Qt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),$("click",Dt,()=>{It()!==r(d)&&xe(It()),le(r(We))}),p(Re,Dt)}),p(Lt,ee)},hr=Lt=>{var ee=Ab();p(Lt,ee)};A(Jt,Lt=>{r(Ja)&&r(la).length===0?Lt(mr):r(la).length>0?Lt(Ir,1):Lt(hr,-1)})}var it=f(Jt,2);{var Zt=Lt=>{var ee=Pb(),Re=i(ee),We=f(i(Re),2),Dt=f(i(We));us(Dt,{size:9});var nr=f(Re,2);{var lr=Ht=>{var or=Nb(),br=i(or),ur=i(br),Mr=i(ur);Tr(Mr,{size:12,class:"animate-spin text-dl-primary-light"});var Br=f(ur,2),za=f(br,2),Nt=i(za),Xt=f(za,2),Va=i(Xt);N(()=>{so(Nt,`width: ${r(E)??""}%`),S(Va,r(re))}),$("click",Br,Se),p(Ht,or)},cr=Ht=>{var or=Lb(),br=te(or),ur=i(br),Mr=f(ur,2),Br=i(Mr);jn(Br,{size:12});var za=f(br,2);we(za,21,()=>ir,ye,(Nt,Xt)=>{const Va=se(()=>r(la).some(tn=>tn===r(Xt).name||tn===r(Xt).name.split(":")[0]));var en=Me(),gl=te(en);{var Ro=tn=>{var hl=Ib(),Ni=i(hl),Oi=i(Ni),Ii=i(Oi),qd=i(Ii),Li=f(Ii,2),$d=i(Li),Fd=f(Li,2);{var Bd=jo=>{var Ri=Ob(),Kd=i(Ri);N(()=>S(Kd,r(Xt).tag)),p(jo,Ri)};A(Fd,jo=>{r(Xt).tag&&jo(Bd)})}var Vd=f(Oi,2),Gd=i(Vd),Hd=f(Ni,2),Pi=i(Hd),Ud=i(Pi),Wd=f(Pi,2);jn(Wd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),N(()=>{S(qd,r(Xt).name),S($d,r(Xt).size),S(Gd,r(Xt).desc),S(Ud,`${r(Xt).gb??""} GB`)}),$("click",hl,()=>{c(L,r(Xt).name,!0),Mt()}),p(tn,hl)};A(gl,tn=>{r(Va)||tn(Ro)})}p(Nt,en)}),N(Nt=>Mr.disabled=Nt,[()=>!r(L).trim()]),$("keydown",ur,Nt=>{Nt.key==="Enter"&&Mt()}),Pn(ur,()=>r(L),Nt=>c(L,Nt)),$("click",Mr,Mt),p(Ht,or)};A(nr,Ht=>{r(U)?Ht(lr):Ht(cr,-1)})}p(Lt,ee)};A(it,Lt=>{It()==="ollama"&&Lt(Zt)})}p(at,At)};A(Zr,at=>{(ke().available||r(Ut)||r(Ur)||ke().auth==="oauth")&&at(ea)})}p(_e,J)};A(tr,_e=>{(r(Gt)||r(Qt))&&_e(dt)})}N((_e,J)=>{Ge($a,1,_e),Ge(ba,1,J),S(Qa,ke().label||It()),S(Ze,ke().desc||"")},[()=>ut(vt("rounded-xl border transition-all",r(Qt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>ut(vt("w-2.5 h-2.5 rounded-full flex-shrink-0",ke().available?"bg-dl-success":r(Ut)?"bg-amber-400":"bg-dl-text-dim"))]),$("click",ma,()=>{ke().available||r(Ut)?It()===r(d)?ct(It()):xe(It()):ct(It())}),p(Rt,$a)});var Oe=f(G,2),_t=i(Oe),K=i(_t);{var oe=Rt=>{var er=sa();N(()=>{var yr;return S(er,`현재: ${(((yr=r(o)[r(d)])==null?void 0:yr.label)||r(d))??""} / ${r(v)??""}`)}),p(Rt,er)},qe=Rt=>{var er=sa();N(()=>{var yr;return S(er,`현재: ${(((yr=r(o)[r(d)])==null?void 0:yr.label)||r(d))??""}`)}),p(Rt,er)};A(K,Rt=>{r(d)&&r(v)?Rt(oe):r(d)&&Rt(qe,1)})}var fr=f(_t,2);pn(u,Rt=>c(lt,Rt),()=>r(lt)),$("click",V,Rt=>{Rt.target===Rt.currentTarget&&c(T,!1)}),$("click",j,()=>c(T,!1)),$("click",fr,()=>c(T,!1)),p(w,V)};A(Ul,w=>{r(T)&&w(Wl)})}var Kl=f(Ul,2);{var Oo=w=>{var V=$b(),u=i(V),b=i(u),z=f(i(b),2),j=i(z);Xn(j,{size:16});var q=f(b,4);bs(q,{get selectedCompany(){return W.selectedCompany},get recentCompanies(){return W.recentCompanies},get activeTab(){return W.activeTab},get evidenceMessage(){return r(Vt)},get activeEvidenceSection(){return W.activeEvidenceSection},get selectedEvidenceIndex(){return W.selectedEvidenceIndex},onSelectCompany:G=>W.selectCompany(G,{pin:!0}),onChangeTab:G=>W.setTab(G),onAskAboutModule:Ot,onNotify:Ne,onClose:zt}),pn(u,G=>c(fe,G),()=>r(fe)),$("click",V,G=>{G.target===G.currentTarget&&zt()}),$("click",z,zt),p(w,V)};A(Kl,w=>{r(Ae)&&W.isOpen&&w(Oo)})}var Yl=f(Kl,2);{var Io=w=>{var V=Fb(),u=i(V),b=f(i(u),4),z=i(b),j=f(z,2);pn(u,q=>c(he,q),()=>r(he)),$("click",V,q=>{q.target===q.currentTarget&&c(ge,null)}),$("click",z,()=>c(ge,null)),$("click",j,Te),p(w,V)};A(Yl,w=>{r(ge)&&w(Io)})}var Lo=f(Yl,2);{var Po=w=>{var V=Bb(),u=i(V),b=i(u),z=i(b),j=f(b,2),q=i(j);Xn(q,{size:14}),N(G=>{Ge(u,1,G),S(z,r(wt))},[()=>ut(vt("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",r(ae)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":r(ae)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),$("click",j,()=>{c(qt,!1)}),p(w,V)};A(Lo,w=>{r(qt)&&w(Po)})}N((w,V)=>{Ge(Ue,1,ut(r(Ae)?r(g)?"sidebar-mobile":"hidden":"")),ka(vr,"aria-label",r(g)?"사이드바 접기":"사이드바 열기"),Ge(xa,1,w),ka(xa,"aria-pressed",W.isOpen),S(Dl,W.isOpen?"패널 닫기":"탐색 열기"),Ge(Un,1,V)},[()=>ut(vt("flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] transition-colors",W.isOpen?"bg-dl-primary/10 text-dl-primary-light":"text-dl-text-dim hover:bg-white/5 hover:text-dl-text-muted")),()=>ut(vt("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",r(C)?"text-dl-text-dim":r($t)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),$("click",vr,Ie),$("click",xa,()=>W.isOpen?zt():Le("explore")),$("click",Un,()=>Fe()),p(e,ht),pa()}Ya(["click","keydown"]);wu(Gb,{target:document.getElementById("app")});
