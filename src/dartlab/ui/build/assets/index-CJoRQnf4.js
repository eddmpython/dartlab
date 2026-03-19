var Hc=Object.defineProperty;var Xi=e=>{throw TypeError(e)};var Kc=(e,t,n)=>t in e?Hc(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n;var An=(e,t,n)=>Kc(e,typeof t!="symbol"?t+"":t,n),Ws=(e,t,n)=>t.has(e)||Xi("Cannot "+n);var A=(e,t,n)=>(Ws(e,t,"read from private field"),n?n.call(e):t.get(e)),it=(e,t,n)=>t.has(e)?Xi("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,n),Ye=(e,t,n,a)=>(Ws(e,t,"write to private field"),a?a.call(e,n):t.set(e,n),n),sr=(e,t,n)=>(Ws(e,t,"access private method"),n);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const o of document.querySelectorAll('link[rel="modulepreload"]'))a(o);new MutationObserver(o=>{for(const i of o)if(i.type==="childList")for(const s of i.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&a(s)}).observe(document,{childList:!0,subtree:!0});function n(o){const i={};return o.integrity&&(i.integrity=o.integrity),o.referrerPolicy&&(i.referrerPolicy=o.referrerPolicy),o.crossOrigin==="use-credentials"?i.credentials="include":o.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function a(o){if(o.ep)return;o.ep=!0;const i=n(o);fetch(o.href,i)}})();const Us=!1;var bi=Array.isArray,Uc=Array.prototype.indexOf,Co=Array.prototype.includes,Ss=Array.from,Yc=Object.defineProperty,Ea=Object.getOwnPropertyDescriptor,zl=Object.getOwnPropertyDescriptors,Xc=Object.prototype,Jc=Array.prototype,_i=Object.getPrototypeOf,Ji=Object.isExtensible;function Ro(e){return typeof e=="function"}const Qc=()=>{};function Zc(e){return e()}function Ys(e){for(var t=0;t<e.length;t++)e[t]()}function El(){var e,t,n=new Promise((a,o)=>{e=a,t=o});return{promise:n,resolve:e,reject:t}}function Pl(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const a of e)if(n.push(a),n.length===t)break;return n}const Ar=2,To=4,no=8,$s=1<<24,Da=16,On=32,io=64,Xs=128,_n=512,Mr=1024,Ir=2048,Ln=4096,Gr=8192,Jn=16384,Ao=32768,fa=65536,Qi=1<<17,eu=1<<18,zo=1<<19,Nl=1<<20,Un=1<<25,ao=65536,Js=1<<21,yi=1<<22,Pa=1<<23,Qn=Symbol("$state"),Ll=Symbol("legacy props"),tu=Symbol(""),Ka=new class extends Error{constructor(){super(...arguments);An(this,"name","StaleReactionError");An(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var Il;const Ol=!!((Il=globalThis.document)!=null&&Il.contentType)&&globalThis.document.contentType.includes("xml");function ru(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function nu(e,t,n){throw new Error("https://svelte.dev/e/each_key_duplicate")}function au(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function ou(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function su(e){throw new Error("https://svelte.dev/e/effect_orphan")}function iu(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function lu(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function du(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function cu(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function uu(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function fu(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const vu=1,pu=2,Rl=4,mu=8,hu=16,xu=1,gu=2,Dl=4,bu=8,_u=16,yu=1,wu=2,vr=Symbol(),jl="http://www.w3.org/1999/xhtml",Wl="http://www.w3.org/2000/svg",ku="http://www.w3.org/1998/Math/MathML",Cu="@attach";function Su(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function $u(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Vl(e){return e===this.v}function Mu(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function ql(e){return!Mu(e,this.v)}let ts=!1,Iu=!1;function Tu(){ts=!0}let pr=null;function So(e){pr=e}function ta(e,t=!1,n){pr={p:pr,i:!1,c:null,e:null,s:e,x:null,l:ts&&!t?{s:null,u:null,$:[]}:null}}function ra(e){var t=pr,n=t.e;if(n!==null){t.e=null;for(var a of n)id(a)}return t.i=!0,pr=t.p,{}}function rs(){return!ts||pr!==null&&pr.l===null}let Ua=[];function Bl(){var e=Ua;Ua=[],Ys(e)}function Zn(e){if(Ua.length===0&&!Ho){var t=Ua;queueMicrotask(()=>{t===Ua&&Bl()})}Ua.push(e)}function Au(){for(;Ua.length>0;)Bl()}function Fl(e){var t=nt;if(t===null)return rt.f|=Pa,e;if((t.f&Ao)===0&&(t.f&To)===0)throw e;Aa(e,t)}function Aa(e,t){for(;t!==null;){if((t.f&Xs)!==0){if((t.f&Ao)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw e}const zu=-7169;function Kt(e,t){e.f=e.f&zu|t}function wi(e){(e.f&_n)!==0||e.deps===null?Kt(e,Mr):Kt(e,Ln)}function Gl(e){if(e!==null)for(const t of e)(t.f&Ar)===0||(t.f&ao)===0||(t.f^=ao,Gl(t.deps))}function Hl(e,t,n){(e.f&Ir)!==0?t.add(e):(e.f&Ln)!==0&&n.add(e),Gl(e.deps),Kt(e,Mr)}const us=new Set;let Xe=null,Qs=null,$r=null,Zr=[],Ms=null,Ho=!1,$o=null,Eu=1;var Ma,ho,Ja,xo,go,bo,Ia,Bn,_o,rn,Zs,ei,ti,ri;const Ni=class Ni{constructor(){it(this,rn);An(this,"id",Eu++);An(this,"current",new Map);An(this,"previous",new Map);it(this,Ma,new Set);it(this,ho,new Set);it(this,Ja,0);it(this,xo,0);it(this,go,null);it(this,bo,new Set);it(this,Ia,new Set);it(this,Bn,new Map);An(this,"is_fork",!1);it(this,_o,!1)}skip_effect(t){A(this,Bn).has(t)||A(this,Bn).set(t,{d:[],m:[]})}unskip_effect(t){var n=A(this,Bn).get(t);if(n){A(this,Bn).delete(t);for(var a of n.d)Kt(a,Ir),Yn(a);for(a of n.m)Kt(a,Ln),Yn(a)}}process(t){var o;Zr=[],this.apply();var n=$o=[],a=[];for(const i of t)sr(this,rn,ei).call(this,i,n,a);if($o=null,sr(this,rn,Zs).call(this)){sr(this,rn,ti).call(this,a),sr(this,rn,ti).call(this,n);for(const[i,s]of A(this,Bn))Xl(i,s)}else{Qs=this,Xe=null;for(const i of A(this,Ma))i(this);A(this,Ma).clear(),A(this,Ja)===0&&sr(this,rn,ri).call(this),Zi(a),Zi(n),A(this,bo).clear(),A(this,Ia).clear(),Qs=null,(o=A(this,go))==null||o.resolve()}$r=null}capture(t,n){n!==vr&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&Pa)===0&&(this.current.set(t,t.v),$r==null||$r.set(t,t.v))}activate(){Xe=this,this.apply()}deactivate(){Xe===this&&(Xe=null,$r=null)}flush(){var t;if(Zr.length>0)Xe=this,Kl();else if(A(this,Ja)===0&&!this.is_fork){for(const n of A(this,Ma))n(this);A(this,Ma).clear(),sr(this,rn,ri).call(this),(t=A(this,go))==null||t.resolve()}this.deactivate()}discard(){for(const t of A(this,ho))t(this);A(this,ho).clear()}increment(t){Ye(this,Ja,A(this,Ja)+1),t&&Ye(this,xo,A(this,xo)+1)}decrement(t){Ye(this,Ja,A(this,Ja)-1),t&&Ye(this,xo,A(this,xo)-1),!A(this,_o)&&(Ye(this,_o,!0),Zn(()=>{Ye(this,_o,!1),sr(this,rn,Zs).call(this)?Zr.length>0&&this.flush():this.revive()}))}revive(){for(const t of A(this,bo))A(this,Ia).delete(t),Kt(t,Ir),Yn(t);for(const t of A(this,Ia))Kt(t,Ln),Yn(t);this.flush()}oncommit(t){A(this,Ma).add(t)}ondiscard(t){A(this,ho).add(t)}settled(){return(A(this,go)??Ye(this,go,El())).promise}static ensure(){if(Xe===null){const t=Xe=new Ni;us.add(Xe),Ho||Zn(()=>{Xe===t&&t.flush()})}return Xe}apply(){}};Ma=new WeakMap,ho=new WeakMap,Ja=new WeakMap,xo=new WeakMap,go=new WeakMap,bo=new WeakMap,Ia=new WeakMap,Bn=new WeakMap,_o=new WeakMap,rn=new WeakSet,Zs=function(){return this.is_fork||A(this,xo)>0},ei=function(t,n,a){t.f^=Mr;for(var o=t.first;o!==null;){var i=o.f,s=(i&(On|io))!==0,l=s&&(i&Mr)!==0,u=(i&Gr)!==0,p=l||A(this,Bn).has(o);if(!p&&o.fn!==null){s?u||(o.f^=Mr):(i&To)!==0?n.push(o):(i&(no|$s))!==0&&u?a.push(o):os(o)&&(Io(o),(i&Da)!==0&&(A(this,Ia).add(o),u&&Kt(o,Ir)));var x=o.first;if(x!==null){o=x;continue}}for(;o!==null;){var _=o.next;if(_!==null){o=_;break}o=o.parent}}},ti=function(t){for(var n=0;n<t.length;n+=1)Hl(t[n],A(this,bo),A(this,Ia))},ri=function(){var i;if(us.size>1){this.previous.clear();var t=Xe,n=$r,a=!0;for(const s of us){if(s===this){a=!1;continue}const l=[];for(const[p,x]of this.current){if(s.current.has(p))if(a&&x!==s.current.get(p))s.current.set(p,x);else continue;l.push(p)}if(l.length===0)continue;const u=[...s.current.keys()].filter(p=>!this.current.has(p));if(u.length>0){var o=Zr;Zr=[];const p=new Set,x=new Map;for(const _ of l)Ul(_,u,p,x);if(Zr.length>0){Xe=s,s.apply();for(const _ of Zr)sr(i=s,rn,ei).call(i,_,[],[]);s.deactivate()}Zr=o}}Xe=t,$r=n}A(this,Bn).clear(),us.delete(this)};let Na=Ni;function Pu(e){var t=Ho;Ho=!0;try{for(var n;;){if(Au(),Zr.length===0&&(Xe==null||Xe.flush(),Zr.length===0))return Ms=null,n;Kl()}}finally{Ho=t}}function Kl(){var e=null;try{for(var t=0;Zr.length>0;){var n=Na.ensure();if(t++>1e3){var a,o;Nu()}n.process(Zr),La.clear()}}finally{Zr=[],Ms=null,$o=null}}function Nu(){try{iu()}catch(e){Aa(e,Ms)}}let zn=null;function Zi(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var a=e[n++];if((a.f&(Jn|Gr))===0&&os(a)&&(zn=new Set,Io(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&ud(a),(zn==null?void 0:zn.size)>0)){La.clear();for(const o of zn){if((o.f&(Jn|Gr))!==0)continue;const i=[o];let s=o.parent;for(;s!==null;)zn.has(s)&&(zn.delete(s),i.push(s)),s=s.parent;for(let l=i.length-1;l>=0;l--){const u=i[l];(u.f&(Jn|Gr))===0&&Io(u)}}zn.clear()}}zn=null}}function Ul(e,t,n,a){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const o of e.reactions){const i=o.f;(i&Ar)!==0?Ul(o,t,n,a):(i&(yi|Da))!==0&&(i&Ir)===0&&Yl(o,t,a)&&(Kt(o,Ir),Yn(o))}}function Yl(e,t,n){const a=n.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const o of e.deps){if(Co.call(t,o))return!0;if((o.f&Ar)!==0&&Yl(o,t,n))return n.set(o,!0),!0}return n.set(e,!1),!1}function Yn(e){var t=Ms=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(To|no|$s))!==0&&(e.f&Ao)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if($o!==null&&t===nt&&(e.f&no)===0)return;if((a&(io|On))!==0){if((a&Mr)===0)return;t.f^=Mr}}Zr.push(t)}function Xl(e,t){if(!((e.f&On)!==0&&(e.f&Mr)!==0)){(e.f&Ir)!==0?t.d.push(e):(e.f&Ln)!==0&&t.m.push(e),Kt(e,Mr);for(var n=e.first;n!==null;)Xl(n,t),n=n.next}}function Lu(e){let t=0,n=Oa(0),a;return()=>{$i()&&(r(n),Ii(()=>(t===0&&(a=oo(()=>e(()=>Uo(n)))),t+=1,()=>{Zn(()=>{t-=1,t===0&&(a==null||a(),a=void 0,Uo(n))})})))}}var Ou=fa|zo;function Ru(e,t,n,a){new Du(e,t,n,a)}var gn,gi,Fn,Qa,Qr,Gn,cn,En,da,Za,Ta,yo,wo,ko,ca,ks,lr,ju,Wu,Vu,ni,hs,xs,ai;class Du{constructor(t,n,a,o){it(this,lr);An(this,"parent");An(this,"is_pending",!1);An(this,"transform_error");it(this,gn);it(this,gi,null);it(this,Fn);it(this,Qa);it(this,Qr);it(this,Gn,null);it(this,cn,null);it(this,En,null);it(this,da,null);it(this,Za,0);it(this,Ta,0);it(this,yo,!1);it(this,wo,new Set);it(this,ko,new Set);it(this,ca,null);it(this,ks,Lu(()=>(Ye(this,ca,Oa(A(this,Za))),()=>{Ye(this,ca,null)})));var i;Ye(this,gn,t),Ye(this,Fn,n),Ye(this,Qa,s=>{var l=nt;l.b=this,l.f|=Xs,a(s)}),this.parent=nt.b,this.transform_error=o??((i=this.parent)==null?void 0:i.transform_error)??(s=>s),Ye(this,Qr,Eo(()=>{sr(this,lr,ni).call(this)},Ou))}defer_effect(t){Hl(t,A(this,wo),A(this,ko))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!A(this,Fn).pending}update_pending_count(t){sr(this,lr,ai).call(this,t),Ye(this,Za,A(this,Za)+t),!(!A(this,ca)||A(this,yo))&&(Ye(this,yo,!0),Zn(()=>{Ye(this,yo,!1),A(this,ca)&&Mo(A(this,ca),A(this,Za))}))}get_effect_pending(){return A(this,ks).call(this),r(A(this,ca))}error(t){var n=A(this,Fn).onerror;let a=A(this,Fn).failed;if(!n&&!a)throw t;A(this,Gn)&&(Tr(A(this,Gn)),Ye(this,Gn,null)),A(this,cn)&&(Tr(A(this,cn)),Ye(this,cn,null)),A(this,En)&&(Tr(A(this,En)),Ye(this,En,null));var o=!1,i=!1;const s=()=>{if(o){$u();return}o=!0,i&&fu(),A(this,En)!==null&&to(A(this,En),()=>{Ye(this,En,null)}),sr(this,lr,xs).call(this,()=>{Na.ensure(),sr(this,lr,ni).call(this)})},l=u=>{try{i=!0,n==null||n(u,s),i=!1}catch(p){Aa(p,A(this,Qr)&&A(this,Qr).parent)}a&&Ye(this,En,sr(this,lr,xs).call(this,()=>{Na.ensure();try{return tn(()=>{var p=nt;p.b=this,p.f|=Xs,a(A(this,gn),()=>u,()=>s)})}catch(p){return Aa(p,A(this,Qr).parent),null}}))};Zn(()=>{var u;try{u=this.transform_error(t)}catch(p){Aa(p,A(this,Qr)&&A(this,Qr).parent);return}u!==null&&typeof u=="object"&&typeof u.then=="function"?u.then(l,p=>Aa(p,A(this,Qr)&&A(this,Qr).parent)):l(u)})}}gn=new WeakMap,gi=new WeakMap,Fn=new WeakMap,Qa=new WeakMap,Qr=new WeakMap,Gn=new WeakMap,cn=new WeakMap,En=new WeakMap,da=new WeakMap,Za=new WeakMap,Ta=new WeakMap,yo=new WeakMap,wo=new WeakMap,ko=new WeakMap,ca=new WeakMap,ks=new WeakMap,lr=new WeakSet,ju=function(){try{Ye(this,Gn,tn(()=>A(this,Qa).call(this,A(this,gn))))}catch(t){this.error(t)}},Wu=function(t){const n=A(this,Fn).failed;n&&Ye(this,En,tn(()=>{n(A(this,gn),()=>t,()=>()=>{})}))},Vu=function(){const t=A(this,Fn).pending;t&&(this.is_pending=!0,Ye(this,cn,tn(()=>t(A(this,gn)))),Zn(()=>{var n=Ye(this,da,document.createDocumentFragment()),a=ea();n.append(a),Ye(this,Gn,sr(this,lr,xs).call(this,()=>(Na.ensure(),tn(()=>A(this,Qa).call(this,a))))),A(this,Ta)===0&&(A(this,gn).before(n),Ye(this,da,null),to(A(this,cn),()=>{Ye(this,cn,null)}),sr(this,lr,hs).call(this))}))},ni=function(){try{if(this.is_pending=this.has_pending_snippet(),Ye(this,Ta,0),Ye(this,Za,0),Ye(this,Gn,tn(()=>{A(this,Qa).call(this,A(this,gn))})),A(this,Ta)>0){var t=Ye(this,da,document.createDocumentFragment());zi(A(this,Gn),t);const n=A(this,Fn).pending;Ye(this,cn,tn(()=>n(A(this,gn))))}else sr(this,lr,hs).call(this)}catch(n){this.error(n)}},hs=function(){this.is_pending=!1;for(const t of A(this,wo))Kt(t,Ir),Yn(t);for(const t of A(this,ko))Kt(t,Ln),Yn(t);A(this,wo).clear(),A(this,ko).clear()},xs=function(t){var n=nt,a=rt,o=pr;kn(A(this,Qr)),wn(A(this,Qr)),So(A(this,Qr).ctx);try{return t()}catch(i){return Fl(i),null}finally{kn(n),wn(a),So(o)}},ai=function(t){var n;if(!this.has_pending_snippet()){this.parent&&sr(n=this.parent,lr,ai).call(n,t);return}Ye(this,Ta,A(this,Ta)+t),A(this,Ta)===0&&(sr(this,lr,hs).call(this),A(this,cn)&&to(A(this,cn),()=>{Ye(this,cn,null)}),A(this,da)&&(A(this,gn).before(A(this,da)),Ye(this,da,null)))};function Jl(e,t,n,a){const o=rs()?ns:ki;var i=e.filter(_=>!_.settled);if(n.length===0&&i.length===0){a(t.map(o));return}var s=nt,l=qu(),u=i.length===1?i[0].promise:i.length>1?Promise.all(i.map(_=>_.promise)):null;function p(_){l();try{a(_)}catch(y){(s.f&Jn)===0&&Aa(y,s)}oi()}if(n.length===0){u.then(()=>p(t.map(o)));return}function x(){l(),Promise.all(n.map(_=>Fu(_))).then(_=>p([...t.map(o),..._])).catch(_=>Aa(_,s))}u?u.then(x):x()}function qu(){var e=nt,t=rt,n=pr,a=Xe;return function(i=!0){kn(e),wn(t),So(n),i&&(a==null||a.activate())}}function oi(e=!0){kn(null),wn(null),So(null),e&&(Xe==null||Xe.deactivate())}function Bu(){var e=nt.b,t=Xe,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}function ns(e){var t=Ar|Ir,n=rt!==null&&(rt.f&Ar)!==0?rt:null;return nt!==null&&(nt.f|=zo),{ctx:pr,deps:null,effects:null,equals:Vl,f:t,fn:e,reactions:null,rv:0,v:vr,wv:0,parent:n??nt,ac:null}}function Fu(e,t,n){nt===null&&ru();var o=void 0,i=Oa(vr),s=!rt,l=new Map;return of(()=>{var y;var u=El();o=u.promise;try{Promise.resolve(e()).then(u.resolve,u.reject).finally(oi)}catch(k){u.reject(k),oi()}var p=Xe;if(s){var x=Bu();(y=l.get(p))==null||y.reject(Ka),l.delete(p),l.set(p,u)}const _=(k,w=void 0)=>{if(p.activate(),w)w!==Ka&&(i.f|=Pa,Mo(i,w));else{(i.f&Pa)!==0&&(i.f^=Pa),Mo(i,k);for(const[E,C]of l){if(l.delete(E),E===p)break;C.reject(Ka)}}x&&x()};u.promise.then(_,k=>_(null,k||"unknown"))}),Ts(()=>{for(const u of l.values())u.reject(Ka)}),new Promise(u=>{function p(x){function _(){x===o?u(i):p(o)}x.then(_,_)}p(o)})}function F(e){const t=ns(e);return pd(t),t}function ki(e){const t=ns(e);return t.equals=ql,t}function Gu(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)Tr(t[n])}}function Hu(e){for(var t=e.parent;t!==null;){if((t.f&Ar)===0)return(t.f&Jn)===0?t:null;t=t.parent}return null}function Ci(e){var t,n=nt;kn(Hu(e));try{e.f&=~ao,Gu(e),t=gd(e)}finally{kn(n)}return t}function Ql(e){var t=Ci(e);if(!e.equals(t)&&(e.wv=hd(),(!(Xe!=null&&Xe.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Kt(e,Mr);return}Ra||($r!==null?($i()||Xe!=null&&Xe.is_fork)&&$r.set(e,t):wi(e))}function Ku(e){var t,n;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(n=a.ac)==null||n.abort(Ka),a.teardown=Qc,a.ac=null,Qo(a,0),Ti(a))}function Zl(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Io(t)}let si=new Set;const La=new Map;let ed=!1;function Oa(e,t){var n={f:0,v:e,reactions:null,equals:Vl,rv:0,wv:0};return n}function G(e,t){const n=Oa(e);return pd(n),n}function Uu(e,t=!1,n=!0){var o;const a=Oa(e);return t||(a.equals=ql),ts&&n&&pr!==null&&pr.l!==null&&((o=pr.l).s??(o.s=[])).push(a),a}function c(e,t,n=!1){rt!==null&&(!Nn||(rt.f&Qi)!==0)&&rs()&&(rt.f&(Ar|Da|yi|Qi))!==0&&(yn===null||!Co.call(yn,e))&&uu();let a=n?Tt(t):t;return Mo(e,a)}function Mo(e,t){if(!e.equals(t)){var n=e.v;Ra?La.set(e,t):La.set(e,n),e.v=t;var a=Na.ensure();if(a.capture(e,n),(e.f&Ar)!==0){const o=e;(e.f&Ir)!==0&&Ci(o),wi(o)}e.wv=hd(),td(e,Ir),rs()&&nt!==null&&(nt.f&Mr)!==0&&(nt.f&(On|io))===0&&(xn===null?lf([e]):xn.push(e)),!a.is_fork&&si.size>0&&!ed&&Yu()}return t}function Yu(){ed=!1;for(const e of si)(e.f&Mr)!==0&&Kt(e,Ln),os(e)&&Io(e);si.clear()}function Ko(e,t=1){var n=r(e),a=t===1?n++:n--;return c(e,n),a}function Uo(e){c(e,e.v+1)}function td(e,t){var n=e.reactions;if(n!==null)for(var a=rs(),o=n.length,i=0;i<o;i++){var s=n[i],l=s.f;if(!(!a&&s===nt)){var u=(l&Ir)===0;if(u&&Kt(s,t),(l&Ar)!==0){var p=s;$r==null||$r.delete(p),(l&ao)===0&&(l&_n&&(s.f|=ao),td(p,Ln))}else u&&((l&Da)!==0&&zn!==null&&zn.add(s),Yn(s))}}}function Tt(e){if(typeof e!="object"||e===null||Qn in e)return e;const t=_i(e);if(t!==Xc&&t!==Jc)return e;var n=new Map,a=bi(e),o=G(0),i=ro,s=l=>{if(ro===i)return l();var u=rt,p=ro;wn(null),nl(i);var x=l();return wn(u),nl(p),x};return a&&n.set("length",G(e.length)),new Proxy(e,{defineProperty(l,u,p){(!("value"in p)||p.configurable===!1||p.enumerable===!1||p.writable===!1)&&du();var x=n.get(u);return x===void 0?s(()=>{var _=G(p.value);return n.set(u,_),_}):c(x,p.value,!0),!0},deleteProperty(l,u){var p=n.get(u);if(p===void 0){if(u in l){const x=s(()=>G(vr));n.set(u,x),Uo(o)}}else c(p,vr),Uo(o);return!0},get(l,u,p){var k;if(u===Qn)return e;var x=n.get(u),_=u in l;if(x===void 0&&(!_||(k=Ea(l,u))!=null&&k.writable)&&(x=s(()=>{var w=Tt(_?l[u]:vr),E=G(w);return E}),n.set(u,x)),x!==void 0){var y=r(x);return y===vr?void 0:y}return Reflect.get(l,u,p)},getOwnPropertyDescriptor(l,u){var p=Reflect.getOwnPropertyDescriptor(l,u);if(p&&"value"in p){var x=n.get(u);x&&(p.value=r(x))}else if(p===void 0){var _=n.get(u),y=_==null?void 0:_.v;if(_!==void 0&&y!==vr)return{enumerable:!0,configurable:!0,value:y,writable:!0}}return p},has(l,u){var y;if(u===Qn)return!0;var p=n.get(u),x=p!==void 0&&p.v!==vr||Reflect.has(l,u);if(p!==void 0||nt!==null&&(!x||(y=Ea(l,u))!=null&&y.writable)){p===void 0&&(p=s(()=>{var k=x?Tt(l[u]):vr,w=G(k);return w}),n.set(u,p));var _=r(p);if(_===vr)return!1}return x},set(l,u,p,x){var Y;var _=n.get(u),y=u in l;if(a&&u==="length")for(var k=p;k<_.v;k+=1){var w=n.get(k+"");w!==void 0?c(w,vr):k in l&&(w=s(()=>G(vr)),n.set(k+"",w))}if(_===void 0)(!y||(Y=Ea(l,u))!=null&&Y.writable)&&(_=s(()=>G(void 0)),c(_,Tt(p)),n.set(u,_));else{y=_.v!==vr;var E=s(()=>Tt(p));c(_,E)}var C=Reflect.getOwnPropertyDescriptor(l,u);if(C!=null&&C.set&&C.set.call(x,p),!y){if(a&&typeof u=="string"){var S=n.get("length"),R=Number(u);Number.isInteger(R)&&R>=S.v&&c(S,R+1)}Uo(o)}return!0},ownKeys(l){r(o);var u=Reflect.ownKeys(l).filter(_=>{var y=n.get(_);return y===void 0||y.v!==vr});for(var[p,x]of n)x.v!==vr&&!(p in l)&&u.push(p);return u},setPrototypeOf(){cu()}})}function el(e){try{if(e!==null&&typeof e=="object"&&Qn in e)return e[Qn]}catch{}return e}function Xu(e,t){return Object.is(el(e),el(t))}var ii,rd,nd,ad;function Ju(){if(ii===void 0){ii=window,rd=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;nd=Ea(t,"firstChild").get,ad=Ea(t,"nextSibling").get,Ji(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Ji(n)&&(n.__t=void 0)}}function ea(e=""){return document.createTextNode(e)}function ua(e){return nd.call(e)}function as(e){return ad.call(e)}function d(e,t){return ua(e)}function Z(e,t=!1){{var n=ua(e);return n instanceof Comment&&n.data===""?as(n):n}}function m(e,t=1,n=!1){let a=e;for(;t--;)a=as(a);return a}function Qu(e){e.textContent=""}function od(){return!1}function Si(e,t,n){return document.createElementNS(t??jl,e,void 0)}function Zu(e,t){if(t){const n=document.body;e.autofocus=!0,Zn(()=>{document.activeElement===n&&e.focus()})}}let tl=!1;function ef(){tl||(tl=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const n of e.target.elements)(t=n.__on_r)==null||t.call(n)})},{capture:!0}))}function Is(e){var t=rt,n=nt;wn(null),kn(null);try{return e()}finally{wn(t),kn(n)}}function tf(e,t,n,a=n){e.addEventListener(t,()=>Is(n));const o=e.__on_r;o?e.__on_r=()=>{o(),a(!0)}:e.__on_r=()=>a(!0),ef()}function sd(e){nt===null&&(rt===null&&su(),ou()),Ra&&au()}function rf(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Rn(e,t){var n=nt;n!==null&&(n.f&Gr)!==0&&(e|=Gr);var a={ctx:pr,deps:null,nodes:null,f:e|Ir|_n,first:null,fn:t,last:null,next:null,parent:n,b:n&&n.b,prev:null,teardown:null,wv:0,ac:null},o=a;if((e&To)!==0)$o!==null?$o.push(a):Yn(a);else if(t!==null){try{Io(a)}catch(s){throw Tr(a),s}o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&zo)===0&&(o=o.first,(e&Da)!==0&&(e&fa)!==0&&o!==null&&(o.f|=fa))}if(o!==null&&(o.parent=n,n!==null&&rf(o,n),rt!==null&&(rt.f&Ar)!==0&&(e&io)===0)){var i=rt;(i.effects??(i.effects=[])).push(o)}return a}function $i(){return rt!==null&&!Nn}function Ts(e){const t=Rn(no,null);return Kt(t,Mr),t.teardown=e,t}function bn(e){sd();var t=nt.f,n=!rt&&(t&On)!==0&&(t&Ao)===0;if(n){var a=pr;(a.e??(a.e=[])).push(e)}else return id(e)}function id(e){return Rn(To|Nl,e)}function nf(e){return sd(),Rn(no|Nl,e)}function af(e){Na.ensure();const t=Rn(io|zo,e);return(n={})=>new Promise(a=>{n.outro?to(t,()=>{Tr(t),a(void 0)}):(Tr(t),a(void 0))})}function Mi(e){return Rn(To,e)}function of(e){return Rn(yi|zo,e)}function Ii(e,t=0){return Rn(no|t,e)}function O(e,t=[],n=[],a=[]){Jl(a,t,n,o=>{Rn(no,()=>e(...o.map(r)))})}function Eo(e,t=0){var n=Rn(Da|t,e);return n}function ld(e,t=0){var n=Rn($s|t,e);return n}function tn(e){return Rn(On|zo,e)}function dd(e){var t=e.teardown;if(t!==null){const n=Ra,a=rt;rl(!0),wn(null);try{t.call(null)}finally{rl(n),wn(a)}}}function Ti(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const o=n.ac;o!==null&&Is(()=>{o.abort(Ka)});var a=n.next;(n.f&io)!==0?n.parent=null:Tr(n,t),n=a}}function sf(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&On)===0&&Tr(t),t=n}}function Tr(e,t=!0){var n=!1;(t||(e.f&eu)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(cd(e.nodes.start,e.nodes.end),n=!0),Ti(e,t&&!n),Qo(e,0),Kt(e,Jn);var a=e.nodes&&e.nodes.t;if(a!==null)for(const i of a)i.stop();dd(e);var o=e.parent;o!==null&&o.first!==null&&ud(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function cd(e,t){for(;e!==null;){var n=e===t?null:as(e);e.remove(),e=n}}function ud(e){var t=e.parent,n=e.prev,a=e.next;n!==null&&(n.next=a),a!==null&&(a.prev=n),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=n))}function to(e,t,n=!0){var a=[];fd(e,a,!0);var o=()=>{n&&Tr(e),t&&t()},i=a.length;if(i>0){var s=()=>--i||o();for(var l of a)l.out(s)}else o()}function fd(e,t,n){if((e.f&Gr)===0){e.f^=Gr;var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)(l.is_global||n)&&t.push(l);for(var o=e.first;o!==null;){var i=o.next,s=(o.f&fa)!==0||(o.f&On)!==0&&(e.f&Da)!==0;fd(o,t,s?n:!1),o=i}}}function Ai(e){vd(e,!0)}function vd(e,t){if((e.f&Gr)!==0){e.f^=Gr;for(var n=e.first;n!==null;){var a=n.next,o=(n.f&fa)!==0||(n.f&On)!==0;vd(n,o?t:!1),n=a}var i=e.nodes&&e.nodes.t;if(i!==null)for(const s of i)(s.is_global||t)&&s.in()}}function zi(e,t){if(e.nodes)for(var n=e.nodes.start,a=e.nodes.end;n!==null;){var o=n===a?null:as(n);t.append(n),n=o}}let gs=!1,Ra=!1;function rl(e){Ra=e}let rt=null,Nn=!1;function wn(e){rt=e}let nt=null;function kn(e){nt=e}let yn=null;function pd(e){rt!==null&&(yn===null?yn=[e]:yn.push(e))}let en=null,dn=0,xn=null;function lf(e){xn=e}let md=1,Ya=0,ro=Ya;function nl(e){ro=e}function hd(){return++md}function os(e){var t=e.f;if((t&Ir)!==0)return!0;if(t&Ar&&(e.f&=~ao),(t&Ln)!==0){for(var n=e.deps,a=n.length,o=0;o<a;o++){var i=n[o];if(os(i)&&Ql(i),i.wv>e.wv)return!0}(t&_n)!==0&&$r===null&&Kt(e,Mr)}return!1}function xd(e,t,n=!0){var a=e.reactions;if(a!==null&&!(yn!==null&&Co.call(yn,e)))for(var o=0;o<a.length;o++){var i=a[o];(i.f&Ar)!==0?xd(i,t,!1):t===i&&(n?Kt(i,Ir):(i.f&Mr)!==0&&Kt(i,Ln),Yn(i))}}function gd(e){var E;var t=en,n=dn,a=xn,o=rt,i=yn,s=pr,l=Nn,u=ro,p=e.f;en=null,dn=0,xn=null,rt=(p&(On|io))===0?e:null,yn=null,So(e.ctx),Nn=!1,ro=++Ya,e.ac!==null&&(Is(()=>{e.ac.abort(Ka)}),e.ac=null);try{e.f|=Js;var x=e.fn,_=x();e.f|=Ao;var y=e.deps,k=Xe==null?void 0:Xe.is_fork;if(en!==null){var w;if(k||Qo(e,dn),y!==null&&dn>0)for(y.length=dn+en.length,w=0;w<en.length;w++)y[dn+w]=en[w];else e.deps=y=en;if($i()&&(e.f&_n)!==0)for(w=dn;w<y.length;w++)((E=y[w]).reactions??(E.reactions=[])).push(e)}else!k&&y!==null&&dn<y.length&&(Qo(e,dn),y.length=dn);if(rs()&&xn!==null&&!Nn&&y!==null&&(e.f&(Ar|Ln|Ir))===0)for(w=0;w<xn.length;w++)xd(xn[w],e);if(o!==null&&o!==e){if(Ya++,o.deps!==null)for(let C=0;C<n;C+=1)o.deps[C].rv=Ya;if(t!==null)for(const C of t)C.rv=Ya;xn!==null&&(a===null?a=xn:a.push(...xn))}return(e.f&Pa)!==0&&(e.f^=Pa),_}catch(C){return Fl(C)}finally{e.f^=Js,en=t,dn=n,xn=a,rt=o,yn=i,So(s),Nn=l,ro=u}}function df(e,t){let n=t.reactions;if(n!==null){var a=Uc.call(n,e);if(a!==-1){var o=n.length-1;o===0?n=t.reactions=null:(n[a]=n[o],n.pop())}}if(n===null&&(t.f&Ar)!==0&&(en===null||!Co.call(en,t))){var i=t;(i.f&_n)!==0&&(i.f^=_n,i.f&=~ao),wi(i),Ku(i),Qo(i,0)}}function Qo(e,t){var n=e.deps;if(n!==null)for(var a=t;a<n.length;a++)df(e,n[a])}function Io(e){var t=e.f;if((t&Jn)===0){Kt(e,Mr);var n=nt,a=gs;nt=e,gs=!0;try{(t&(Da|$s))!==0?sf(e):Ti(e),dd(e);var o=gd(e);e.teardown=typeof o=="function"?o:null,e.wv=md;var i;Us&&Iu&&(e.f&Ir)!==0&&e.deps}finally{gs=a,nt=n}}}async function cf(){await Promise.resolve(),Pu()}function r(e){var t=e.f,n=(t&Ar)!==0;if(rt!==null&&!Nn){var a=nt!==null&&(nt.f&Jn)!==0;if(!a&&(yn===null||!Co.call(yn,e))){var o=rt.deps;if((rt.f&Js)!==0)e.rv<Ya&&(e.rv=Ya,en===null&&o!==null&&o[dn]===e?dn++:en===null?en=[e]:en.push(e));else{(rt.deps??(rt.deps=[])).push(e);var i=e.reactions;i===null?e.reactions=[rt]:Co.call(i,rt)||i.push(rt)}}}if(Ra&&La.has(e))return La.get(e);if(n){var s=e;if(Ra){var l=s.v;return((s.f&Mr)===0&&s.reactions!==null||_d(s))&&(l=Ci(s)),La.set(s,l),l}var u=(s.f&_n)===0&&!Nn&&rt!==null&&(gs||(rt.f&_n)!==0),p=(s.f&Ao)===0;os(s)&&(u&&(s.f|=_n),Ql(s)),u&&!p&&(Zl(s),bd(s))}if($r!=null&&$r.has(e))return $r.get(e);if((e.f&Pa)!==0)throw e.v;return e.v}function bd(e){if(e.f|=_n,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&Ar)!==0&&(t.f&_n)===0&&(Zl(t),bd(t))}function _d(e){if(e.v===vr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(La.has(t)||(t.f&Ar)!==0&&_d(t))return!0;return!1}function oo(e){var t=Nn;try{return Nn=!0,e()}finally{Nn=t}}function Ga(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(Qn in e)li(e);else if(!Array.isArray(e))for(let t in e){const n=e[t];typeof n=="object"&&n&&Qn in n&&li(n)}}}function li(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{li(e[a],t)}catch{}const n=_i(e);if(n!==Object.prototype&&n!==Array.prototype&&n!==Map.prototype&&n!==Set.prototype&&n!==Date.prototype){const a=zl(n);for(let o in a){const i=a[o].get;if(i)try{i.call(e)}catch{}}}}}function uf(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const ff=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function vf(e){return ff.includes(e)}const pf={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function mf(e){return e=e.toLowerCase(),pf[e]??e}const hf=["touchstart","touchmove"];function xf(e){return hf.includes(e)}const Xa=Symbol("events"),yd=new Set,di=new Set;function wd(e,t,n,a={}){function o(i){if(a.capture||ci.call(t,i),!i.cancelBubble)return Is(()=>n==null?void 0:n.call(this,i))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Zn(()=>{t.addEventListener(e,o,a)}):t.addEventListener(e,o,a),o}function qn(e,t,n,a,o){var i={capture:a,passive:o},s=wd(e,t,n,i);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Ts(()=>{t.removeEventListener(e,s,i)})}function Q(e,t,n){(t[Xa]??(t[Xa]={}))[e]=n}function lo(e){for(var t=0;t<e.length;t++)yd.add(e[t]);for(var n of di)n(e)}let al=null;function ci(e){var C,S;var t=this,n=t.ownerDocument,a=e.type,o=((C=e.composedPath)==null?void 0:C.call(e))||[],i=o[0]||e.target;al=e;var s=0,l=al===e&&e[Xa];if(l){var u=o.indexOf(l);if(u!==-1&&(t===document||t===window)){e[Xa]=t;return}var p=o.indexOf(t);if(p===-1)return;u<=p&&(s=u)}if(i=o[s]||e.target,i!==t){Yc(e,"currentTarget",{configurable:!0,get(){return i||n}});var x=rt,_=nt;wn(null),kn(null);try{for(var y,k=[];i!==null;){var w=i.assignedSlot||i.parentNode||i.host||null;try{var E=(S=i[Xa])==null?void 0:S[a];E!=null&&(!i.disabled||e.target===i)&&E.call(i,e)}catch(R){y?k.push(R):y=R}if(e.cancelBubble||w===t||w===null)break;i=w}if(y){for(let R of k)queueMicrotask(()=>{throw R});throw y}}finally{e[Xa]=t,delete e.currentTarget,wn(x),kn(_)}}}var Tl;const Vs=((Tl=globalThis==null?void 0:globalThis.window)==null?void 0:Tl.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function gf(e){return(Vs==null?void 0:Vs.createHTML(e))??e}function kd(e){var t=Si("template");return t.innerHTML=gf(e.replaceAll("<!>","<!---->")),t.content}function so(e,t){var n=nt;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function g(e,t){var n=(t&yu)!==0,a=(t&wu)!==0,o,i=!e.startsWith("<!>");return()=>{o===void 0&&(o=kd(i?e:"<!>"+e),n||(o=ua(o)));var s=a||rd?document.importNode(o,!0):o.cloneNode(!0);if(n){var l=ua(s),u=s.lastChild;so(l,u)}else so(s,s);return s}}function bf(e,t,n="svg"){var a=!e.startsWith("<!>"),o=`<${n}>${a?e:"<!>"+e}</${n}>`,i;return()=>{if(!i){var s=kd(o),l=ua(s);i=ua(l)}var u=i.cloneNode(!0);return so(u,u),u}}function _f(e,t){return bf(e,t,"svg")}function $a(e=""){{var t=ea(e+"");return so(t,t),t}}function be(){var e=document.createDocumentFragment(),t=document.createComment(""),n=ea();return e.append(t,n),so(t,n),e}function v(e,t){e!==null&&e.before(t)}function L(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function yf(e,t){return wf(e,t)}const fs=new Map;function wf(e,{target:t,anchor:n,props:a={},events:o,context:i,intro:s=!0,transformError:l}){Ju();var u=void 0,p=af(()=>{var x=n??t.appendChild(ea());Ru(x,{pending:()=>{}},k=>{ta({});var w=pr;i&&(w.c=i),o&&(a.$$events=o),u=e(k,a)||{},ra()},l);var _=new Set,y=k=>{for(var w=0;w<k.length;w++){var E=k[w];if(!_.has(E)){_.add(E);var C=xf(E);for(const Y of[t,document]){var S=fs.get(Y);S===void 0&&(S=new Map,fs.set(Y,S));var R=S.get(E);R===void 0?(Y.addEventListener(E,ci,{passive:C}),S.set(E,1)):S.set(E,R+1)}}}};return y(Ss(yd)),di.add(y),()=>{var C;for(var k of _)for(const S of[t,document]){var w=fs.get(S),E=w.get(k);--E==0?(S.removeEventListener(k,ci),w.delete(k),w.size===0&&fs.delete(S)):w.set(k,E)}di.delete(y),x!==n&&((C=x.parentNode)==null||C.removeChild(x))}});return kf.set(u,p),u}let kf=new WeakMap;var Pn,Hn,un,eo,Zo,es,Cs;class As{constructor(t,n=!0){An(this,"anchor");it(this,Pn,new Map);it(this,Hn,new Map);it(this,un,new Map);it(this,eo,new Set);it(this,Zo,!0);it(this,es,t=>{if(A(this,Pn).has(t)){var n=A(this,Pn).get(t),a=A(this,Hn).get(n);if(a)Ai(a),A(this,eo).delete(n);else{var o=A(this,un).get(n);o&&(o.effect.f&Gr)===0&&(A(this,Hn).set(n,o.effect),A(this,un).delete(n),o.fragment.lastChild.remove(),this.anchor.before(o.fragment),a=o.effect)}for(const[i,s]of A(this,Pn)){if(A(this,Pn).delete(i),i===t)break;const l=A(this,un).get(s);l&&(Tr(l.effect),A(this,un).delete(s))}for(const[i,s]of A(this,Hn)){if(i===n||A(this,eo).has(i)||(s.f&Gr)!==0)continue;const l=()=>{if(Array.from(A(this,Pn).values()).includes(i)){var p=document.createDocumentFragment();zi(s,p),p.append(ea()),A(this,un).set(i,{effect:s,fragment:p})}else Tr(s);A(this,eo).delete(i),A(this,Hn).delete(i)};A(this,Zo)||!a?(A(this,eo).add(i),to(s,l,!1)):l()}}});it(this,Cs,t=>{A(this,Pn).delete(t);const n=Array.from(A(this,Pn).values());for(const[a,o]of A(this,un))n.includes(a)||(Tr(o.effect),A(this,un).delete(a))});this.anchor=t,Ye(this,Zo,n)}ensure(t,n){var a=Xe,o=od();if(n&&!A(this,Hn).has(t)&&!A(this,un).has(t))if(o){var i=document.createDocumentFragment(),s=ea();i.append(s),A(this,un).set(t,{effect:tn(()=>n(s)),fragment:i})}else A(this,Hn).set(t,tn(()=>n(this.anchor)));if(A(this,Pn).set(a,t),o){for(const[l,u]of A(this,Hn))l===t?a.unskip_effect(u):a.skip_effect(u);for(const[l,u]of A(this,un))l===t?a.unskip_effect(u.effect):a.skip_effect(u.effect);a.oncommit(A(this,es)),a.ondiscard(A(this,Cs))}else A(this,es).call(this,a)}}Pn=new WeakMap,Hn=new WeakMap,un=new WeakMap,eo=new WeakMap,Zo=new WeakMap,es=new WeakMap,Cs=new WeakMap;function I(e,t,n=!1){var a=new As(e),o=n?fa:0;function i(s,l){a.ensure(s,l)}Eo(()=>{var s=!1;t((l,u=0)=>{s=!0,i(u,l)}),s||i(-1,null)},o)}function Ae(e,t){return t}function Cf(e,t,n){for(var a=[],o=t.length,i,s=t.length,l=0;l<o;l++){let _=t[l];to(_,()=>{if(i){if(i.pending.delete(_),i.done.add(_),i.pending.size===0){var y=e.outrogroups;ui(e,Ss(i.done)),y.delete(i),y.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var u=a.length===0&&n!==null;if(u){var p=n,x=p.parentNode;Qu(x),x.append(p),e.items.clear()}ui(e,t,!u)}else i={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(i)}function ui(e,t,n=!0){var a;if(e.pending.size>0){a=new Set;for(const s of e.pending.values())for(const l of s)a.add(e.items.get(l).e)}for(var o=0;o<t.length;o++){var i=t[o];if(a!=null&&a.has(i)){i.f|=Un;const s=document.createDocumentFragment();zi(i,s)}else Tr(t[o],n)}}var ol;function ze(e,t,n,a,o,i=null){var s=e,l=new Map,u=(t&Rl)!==0;if(u){var p=e;s=p.appendChild(ea())}var x=null,_=ki(()=>{var Y=n();return bi(Y)?Y:Y==null?[]:Ss(Y)}),y,k=new Map,w=!0;function E(Y){(R.effect.f&Jn)===0&&(R.pending.delete(Y),R.fallback=x,Sf(R,y,s,t,a),x!==null&&(y.length===0?(x.f&Un)===0?Ai(x):(x.f^=Un,Fo(x,null,s)):to(x,()=>{x=null})))}function C(Y){R.pending.delete(Y)}var S=Eo(()=>{y=r(_);for(var Y=y.length,T=new Set,H=Xe,ve=od(),se=0;se<Y;se+=1){var $=y[se],ee=a($,se),ce=w?null:l.get(ee);ce?(ce.v&&Mo(ce.v,$),ce.i&&Mo(ce.i,se),ve&&H.unskip_effect(ce.e)):(ce=$f(l,w?s:ol??(ol=ea()),$,ee,se,o,t,n),w||(ce.e.f|=Un),l.set(ee,ce)),T.add(ee)}if(Y===0&&i&&!x&&(w?x=tn(()=>i(s)):(x=tn(()=>i(ol??(ol=ea()))),x.f|=Un)),Y>T.size&&nu(),!w)if(k.set(H,T),ve){for(const[re,z]of l)T.has(re)||H.skip_effect(z.e);H.oncommit(E),H.ondiscard(C)}else E(H);r(_)}),R={effect:S,items:l,pending:k,outrogroups:null,fallback:x};w=!1}function Do(e){for(;e!==null&&(e.f&On)===0;)e=e.next;return e}function Sf(e,t,n,a,o){var ce,re,z,we,he,ye,Me,ft,ct;var i=(a&mu)!==0,s=t.length,l=e.items,u=Do(e.effect.first),p,x=null,_,y=[],k=[],w,E,C,S;if(i)for(S=0;S<s;S+=1)w=t[S],E=o(w,S),C=l.get(E).e,(C.f&Un)===0&&((re=(ce=C.nodes)==null?void 0:ce.a)==null||re.measure(),(_??(_=new Set)).add(C));for(S=0;S<s;S+=1){if(w=t[S],E=o(w,S),C=l.get(E).e,e.outrogroups!==null)for(const Ce of e.outrogroups)Ce.pending.delete(C),Ce.done.delete(C);if((C.f&Un)!==0)if(C.f^=Un,C===u)Fo(C,null,n);else{var R=x?x.next:u;C===e.effect.last&&(e.effect.last=C.prev),C.prev&&(C.prev.next=C.next),C.next&&(C.next.prev=C.prev),ka(e,x,C),ka(e,C,R),Fo(C,R,n),x=C,y=[],k=[],u=Do(x.next);continue}if((C.f&Gr)!==0&&(Ai(C),i&&((we=(z=C.nodes)==null?void 0:z.a)==null||we.unfix(),(_??(_=new Set)).delete(C))),C!==u){if(p!==void 0&&p.has(C)){if(y.length<k.length){var Y=k[0],T;x=Y.prev;var H=y[0],ve=y[y.length-1];for(T=0;T<y.length;T+=1)Fo(y[T],Y,n);for(T=0;T<k.length;T+=1)p.delete(k[T]);ka(e,H.prev,ve.next),ka(e,x,H),ka(e,ve,Y),u=Y,x=ve,S-=1,y=[],k=[]}else p.delete(C),Fo(C,u,n),ka(e,C.prev,C.next),ka(e,C,x===null?e.effect.first:x.next),ka(e,x,C),x=C;continue}for(y=[],k=[];u!==null&&u!==C;)(p??(p=new Set)).add(u),k.push(u),u=Do(u.next);if(u===null)continue}(C.f&Un)===0&&y.push(C),x=C,u=Do(C.next)}if(e.outrogroups!==null){for(const Ce of e.outrogroups)Ce.pending.size===0&&(ui(e,Ss(Ce.done)),(he=e.outrogroups)==null||he.delete(Ce));e.outrogroups.size===0&&(e.outrogroups=null)}if(u!==null||p!==void 0){var se=[];if(p!==void 0)for(C of p)(C.f&Gr)===0&&se.push(C);for(;u!==null;)(u.f&Gr)===0&&u!==e.fallback&&se.push(u),u=Do(u.next);var $=se.length;if($>0){var ee=(a&Rl)!==0&&s===0?n:null;if(i){for(S=0;S<$;S+=1)(Me=(ye=se[S].nodes)==null?void 0:ye.a)==null||Me.measure();for(S=0;S<$;S+=1)(ct=(ft=se[S].nodes)==null?void 0:ft.a)==null||ct.fix()}Cf(e,se,ee)}}i&&Zn(()=>{var Ce,X;if(_!==void 0)for(C of _)(X=(Ce=C.nodes)==null?void 0:Ce.a)==null||X.apply()})}function $f(e,t,n,a,o,i,s,l){var u=(s&vu)!==0?(s&hu)===0?Uu(n,!1,!1):Oa(n):null,p=(s&pu)!==0?Oa(o):null;return{v:u,i:p,e:tn(()=>(i(t,u??n,p??o,l),()=>{e.delete(a)}))}}function Fo(e,t,n){if(e.nodes)for(var a=e.nodes.start,o=e.nodes.end,i=t&&(t.f&Un)===0?t.nodes.start:n;a!==null;){var s=as(a);if(i.before(a),a===o)return;a=s}}function ka(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function po(e,t,n=!1,a=!1,o=!1){var i=e,s="";O(()=>{var l=nt;if(s!==(s=t()??"")&&(l.nodes!==null&&(cd(l.nodes.start,l.nodes.end),l.nodes=null),s!=="")){var u=n?Wl:a?ku:void 0,p=Si(n?"svg":a?"math":"template",u);p.innerHTML=s;var x=n||a?p:p.content;if(so(ua(x),x.lastChild),n||a)for(;ua(x);)i.before(ua(x));else i.before(x)}})}function Ee(e,t,n,a,o){var l;var i=(l=t.$$slots)==null?void 0:l[n],s=!1;i===!0&&(i=t.children,s=!0),i===void 0||i(e,s?()=>a:a)}function fi(e,t,...n){var a=new As(e);Eo(()=>{const o=t()??null;a.ensure(o,o&&(i=>o(i,...n)))},fa)}function Mf(e,t,n){var a=new As(e);Eo(()=>{var o=t()??null;a.ensure(o,o&&(i=>n(i,o)))},fa)}function If(e,t,n,a,o,i){var s=null,l=e,u=new As(l,!1);Eo(()=>{const p=t()||null;var x=Wl;if(p===null){u.ensure(null,null);return}return u.ensure(p,_=>{if(p){if(s=Si(p,x),so(s,s),a){var y=s.appendChild(ea());a(s,y)}nt.nodes.end=s,_.before(s)}}),()=>{}},fa),Ts(()=>{})}function Tf(e,t){var n=void 0,a;ld(()=>{n!==(n=t())&&(a&&(Tr(a),a=null),n&&(a=tn(()=>{Mi(()=>n(e))})))})}function Cd(e){var t,n,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var o=e.length;for(t=0;t<o;t++)e[t]&&(n=Cd(e[t]))&&(a&&(a+=" "),a+=n)}else for(n in e)e[n]&&(a&&(a+=" "),a+=n);return a}function Sd(){for(var e,t,n=0,a="",o=arguments.length;n<o;n++)(e=arguments[n])&&(t=Cd(e))&&(a&&(a+=" "),a+=t);return a}function vt(e){return typeof e=="object"?Sd(e):e??""}const sl=[...` 	
\r\f \v\uFEFF`];function Af(e,t,n){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),n){for(var o of Object.keys(n))if(n[o])a=a?a+" "+o:o;else if(a.length)for(var i=o.length,s=0;(s=a.indexOf(o,s))>=0;){var l=s+i;(s===0||sl.includes(a[s-1]))&&(l===a.length||sl.includes(a[l]))?a=(s===0?"":a.substring(0,s))+a.substring(l+1):s=l}}return a===""?null:a}function il(e,t=!1){var n=t?" !important;":";",a="";for(var o of Object.keys(e)){var i=e[o];i!=null&&i!==""&&(a+=" "+o+": "+i+n)}return a}function qs(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function zf(e,t){if(t){var n="",a,o;if(Array.isArray(t)?(a=t[0],o=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var i=!1,s=0,l=!1,u=[];a&&u.push(...Object.keys(a).map(qs)),o&&u.push(...Object.keys(o).map(qs));var p=0,x=-1;const E=e.length;for(var _=0;_<E;_++){var y=e[_];if(l?y==="/"&&e[_-1]==="*"&&(l=!1):i?i===y&&(i=!1):y==="/"&&e[_+1]==="*"?l=!0:y==='"'||y==="'"?i=y:y==="("?s++:y===")"&&s--,!l&&i===!1&&s===0){if(y===":"&&x===-1)x=_;else if(y===";"||_===E-1){if(x!==-1){var k=qs(e.substring(p,x).trim());if(!u.includes(k)){y!==";"&&_++;var w=e.substring(p,_).trim();n+=" "+w+";"}}p=_+1,x=-1}}}}return a&&(n+=il(a)),o&&(n+=il(o,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function ke(e,t,n,a,o,i){var s=e.__className;if(s!==n||s===void 0){var l=Af(n,a,i);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=n}else if(i&&o!==i)for(var u in i){var p=!!i[u];(o==null||p!==!!o[u])&&e.classList.toggle(u,p)}return i}function Bs(e,t={},n,a){for(var o in n){var i=n[o];t[o]!==i&&(n[o]==null?e.style.removeProperty(o):e.style.setProperty(o,i,a))}}function $d(e,t,n,a){var o=e.__style;if(o!==t){var i=zf(t,a);i==null?e.removeAttribute("style"):e.style.cssText=i,e.__style=t}else a&&(Array.isArray(a)?(Bs(e,n==null?void 0:n[0],a[0]),Bs(e,n==null?void 0:n[1],a[1],"important")):Bs(e,n,a));return a}function vi(e,t,n=!1){if(e.multiple){if(t==null)return;if(!bi(t))return Su();for(var a of e.options)a.selected=t.includes(ll(a));return}for(a of e.options){var o=ll(a);if(Xu(o,t)){a.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function Ef(e){var t=new MutationObserver(()=>{vi(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Ts(()=>{t.disconnect()})}function ll(e){return"__value"in e?e.__value:e.value}const jo=Symbol("class"),Wo=Symbol("style"),Md=Symbol("is custom element"),Id=Symbol("is html"),Pf=Ol?"option":"OPTION",Nf=Ol?"select":"SELECT";function Lf(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function Fr(e,t,n,a){var o=Td(e);o[t]!==(o[t]=n)&&(t==="loading"&&(e[tu]=n),n==null?e.removeAttribute(t):typeof n!="string"&&Ad(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Of(e,t,n,a,o=!1,i=!1){var s=Td(e),l=s[Md],u=!s[Id],p=t||{},x=e.nodeName===Pf;for(var _ in t)_ in n||(n[_]=null);n.class?n.class=vt(n.class):n[jo]&&(n.class=null),n[Wo]&&(n.style??(n.style=null));var y=Ad(e);for(const T in n){let H=n[T];if(x&&T==="value"&&H==null){e.value=e.__value="",p[T]=H;continue}if(T==="class"){var k=e.namespaceURI==="http://www.w3.org/1999/xhtml";ke(e,k,H,a,t==null?void 0:t[jo],n[jo]),p[T]=H,p[jo]=n[jo];continue}if(T==="style"){$d(e,H,t==null?void 0:t[Wo],n[Wo]),p[T]=H,p[Wo]=n[Wo];continue}var w=p[T];if(!(H===w&&!(H===void 0&&e.hasAttribute(T)))){p[T]=H;var E=T[0]+T[1];if(E!=="$$")if(E==="on"){const ve={},se="$$"+T;let $=T.slice(2);var C=vf($);if(uf($)&&($=$.slice(0,-7),ve.capture=!0),!C&&w){if(H!=null)continue;e.removeEventListener($,p[se],ve),p[se]=null}if(C)Q($,e,H),lo([$]);else if(H!=null){let ee=function(ce){p[T].call(this,ce)};var Y=ee;p[se]=wd($,e,ee,ve)}}else if(T==="style")Fr(e,T,H);else if(T==="autofocus")Zu(e,!!H);else if(!l&&(T==="__value"||T==="value"&&H!=null))e.value=e.__value=H;else if(T==="selected"&&x)Lf(e,H);else{var S=T;u||(S=mf(S));var R=S==="defaultValue"||S==="defaultChecked";if(H==null&&!l&&!R)if(s[T]=null,S==="value"||S==="checked"){let ve=e;const se=t===void 0;if(S==="value"){let $=ve.defaultValue;ve.removeAttribute(S),ve.defaultValue=$,ve.value=ve.__value=se?$:null}else{let $=ve.defaultChecked;ve.removeAttribute(S),ve.defaultChecked=$,ve.checked=se?$:!1}}else e.removeAttribute(T);else R||y.includes(S)&&(l||typeof H!="string")?(e[S]=H,S in s&&(s[S]=vr)):typeof H!="function"&&Fr(e,S,H)}}}return p}function _s(e,t,n=[],a=[],o=[],i,s=!1,l=!1){Jl(o,n,a,u=>{var p=void 0,x={},_=e.nodeName===Nf,y=!1;if(ld(()=>{var w=t(...u.map(r)),E=Of(e,p,w,i,s,l);y&&_&&"value"in w&&vi(e,w.value);for(let S of Object.getOwnPropertySymbols(x))w[S]||Tr(x[S]);for(let S of Object.getOwnPropertySymbols(w)){var C=w[S];S.description===Cu&&(!p||C!==p[S])&&(x[S]&&Tr(x[S]),x[S]=tn(()=>Tf(e,()=>C))),E[S]=C}p=E}),_){var k=e;Mi(()=>{vi(k,p.value,!0),Ef(k)})}y=!0})}function Td(e){return e.__attributes??(e.__attributes={[Md]:e.nodeName.includes("-"),[Id]:e.namespaceURI===jl})}var dl=new Map;function Ad(e){var t=e.getAttribute("is")||e.nodeName,n=dl.get(t);if(n)return n;dl.set(t,n=[]);for(var a,o=e,i=Element.prototype;i!==o;){a=zl(o);for(var s in a)a[s].set&&n.push(s);o=_i(o)}return n}function mo(e,t,n=t){var a=new WeakSet;tf(e,"input",async o=>{var i=o?e.defaultValue:e.value;if(i=Fs(e)?Gs(i):i,n(i),Xe!==null&&a.add(Xe),await cf(),i!==(i=t())){var s=e.selectionStart,l=e.selectionEnd,u=e.value.length;if(e.value=i??"",l!==null){var p=e.value.length;s===l&&l===u&&p>u?(e.selectionStart=p,e.selectionEnd=p):(e.selectionStart=s,e.selectionEnd=Math.min(l,p))}}}),oo(t)==null&&e.value&&(n(Fs(e)?Gs(e.value):e.value),Xe!==null&&a.add(Xe)),Ii(()=>{var o=t();if(e===document.activeElement){var i=Qs??Xe;if(a.has(i))return}Fs(e)&&o===Gs(e.value)||e.type==="date"&&!o&&!e.value||o!==e.value&&(e.value=o??"")})}function Fs(e){var t=e.type;return t==="number"||t==="range"}function Gs(e){return e===""?null:+e}function cl(e,t){return e===t||(e==null?void 0:e[Qn])===t}function za(e={},t,n,a){return Mi(()=>{var o,i;return Ii(()=>{o=i,i=[],oo(()=>{e!==n(...i)&&(t(e,...i),o&&cl(n(...o),e)&&t(null,...o))})}),()=>{Zn(()=>{i&&cl(n(...i),e)&&t(null,...i)})}}),e}function Rf(e=!1){const t=pr,n=t.l.u;if(!n)return;let a=()=>Ga(t.s);if(e){let o=0,i={};const s=ns(()=>{let l=!1;const u=t.s;for(const p in u)u[p]!==i[p]&&(i[p]=u[p],l=!0);return l&&o++,o});a=()=>r(s)}n.b.length&&nf(()=>{ul(t,a),Ys(n.b)}),bn(()=>{const o=oo(()=>n.m.map(Zc));return()=>{for(const i of o)typeof i=="function"&&i()}}),n.a.length&&bn(()=>{ul(t,a),Ys(n.a)})}function ul(e,t){if(e.l.s)for(const n of e.l.s)r(n);t()}let vs=!1;function Df(e){var t=vs;try{return vs=!1,[e(),vs]}finally{vs=t}}const jf={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Wf(e,t,n){return new Proxy({props:e,exclude:t},jf)}const Vf={get(e,t){if(!e.exclude.includes(t))return r(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,n){if(!(t in e.special)){var a=nt;try{kn(e.parent_effect),e.special[t]=Ot({get[t](){return e.props[t]}},t,Dl)}finally{kn(a)}}return e.special[t](n),Ko(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),Ko(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function $e(e,t){return new Proxy({props:e,exclude:t,special:{},version:Oa(0),parent_effect:nt},Vf)}const qf={get(e,t){let n=e.props.length;for(;n--;){let a=e.props[n];if(Ro(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,n){let a=e.props.length;for(;a--;){let o=e.props[a];Ro(o)&&(o=o());const i=Ea(o,t);if(i&&i.set)return i.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let a=e.props[n];if(Ro(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const o=Ea(a,t);return o&&!o.configurable&&(o.configurable=!0),o}}},has(e,t){if(t===Qn||t===Ll)return!1;for(let n of e.props)if(Ro(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(Ro(n)&&(n=n()),!!n){for(const a in n)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(n))t.includes(a)||t.push(a)}return t}};function Ne(...e){return new Proxy({props:e},qf)}function Ot(e,t,n,a){var Y;var o=!ts||(n&gu)!==0,i=(n&bu)!==0,s=(n&_u)!==0,l=a,u=!0,p=()=>(u&&(u=!1,l=s?oo(a):a),l),x;if(i){var _=Qn in e||Ll in e;x=((Y=Ea(e,t))==null?void 0:Y.set)??(_&&t in e?T=>e[t]=T:void 0)}var y,k=!1;i?[y,k]=Df(()=>e[t]):y=e[t],y===void 0&&a!==void 0&&(y=p(),x&&(o&&lu(),x(y)));var w;if(o?w=()=>{var T=e[t];return T===void 0?p():(u=!0,T)}:w=()=>{var T=e[t];return T!==void 0&&(l=void 0),T===void 0?l:T},o&&(n&Dl)===0)return w;if(x){var E=e.$$legacy;return(function(T,H){return arguments.length>0?((!o||!H||E||k)&&x(H?w():T),T):w()})}var C=!1,S=((n&xu)!==0?ns:ki)(()=>(C=!1,w()));i&&r(S);var R=nt;return(function(T,H){if(arguments.length>0){const ve=H?r(S):o&&i?Tt(T):T;return c(S,ve),C=!0,l!==void 0&&(l=ve),T}return Ra&&C||(R.f&Jn)!==0?S.v:r(S)})}const Bf="5";var Al;typeof window<"u"&&((Al=window.__svelte??(window.__svelte={})).v??(Al.v=new Set)).add(Bf);const va="";async function Ff(){const e=await fetch(`${va}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function Gf(e,t=null,n=null){const a={provider:e};t&&(a.model=t),n&&(a.api_key=n);const o=await fetch(`${va}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!o.ok)throw new Error("설정 실패");return o.json()}async function Hf(e){const t=await fetch(`${va}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function Kf(e,{onProgress:t,onDone:n,onError:a}){const o=new AbortController;return fetch(`${va}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:o.signal}).then(async i=>{if(!i.ok){a==null||a("다운로드 실패");return}const s=i.body.getReader(),l=new TextDecoder;let u="";for(;;){const{done:p,value:x}=await s.read();if(p)break;u+=l.decode(x,{stream:!0});const _=u.split(`
`);u=_.pop()||"";for(const y of _)if(y.startsWith("data:"))try{const k=JSON.parse(y.slice(5).trim());k.total&&k.completed!==void 0?t==null||t({total:k.total,completed:k.completed,status:k.status}):k.status&&(t==null||t({status:k.status}))}catch{}}n==null||n()}).catch(i=>{i.name!=="AbortError"&&(a==null||a(i.message))}),{abort:()=>o.abort()}}async function Uf(){const e=await fetch(`${va}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function zd(e){const t=await fetch(`${va}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function Yf(e,t){const n=await fetch(`${va}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!n.ok)throw new Error("company topic 일괄 조회 실패");return n.json()}async function Xf(e){const t=await fetch(`${va}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}function Jf(e,t,n={},{onMeta:a,onSnapshot:o,onContext:i,onSystemPrompt:s,onToolCall:l,onToolResult:u,onChunk:p,onDone:x,onError:_},y=null){const k={question:t,stream:!0,...n};e&&(k.company=e),y&&y.length>0&&(k.history=y);const w=new AbortController;return fetch(`${va}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(k),signal:w.signal}).then(async E=>{if(!E.ok){const H=await E.json().catch(()=>({}));_==null||_(H.detail||"스트리밍 실패");return}const C=E.body.getReader(),S=new TextDecoder;let R="",Y=!1,T=null;for(;;){const{done:H,value:ve}=await C.read();if(H)break;R+=S.decode(ve,{stream:!0});const se=R.split(`
`);R=se.pop()||"";for(const $ of se)if($.startsWith("event:"))T=$.slice(6).trim();else if($.startsWith("data:")&&T){const ee=$.slice(5).trim();try{const ce=JSON.parse(ee);T==="meta"?a==null||a(ce):T==="snapshot"?o==null||o(ce):T==="context"?i==null||i(ce):T==="system_prompt"?s==null||s(ce):T==="tool_call"?l==null||l(ce):T==="tool_result"?u==null||u(ce):T==="chunk"?p==null||p(ce.text):T==="error"?_==null||_(ce.error,ce.action,ce.detail):T==="done"&&(Y||(Y=!0,x==null||x()))}catch{}T=null}}Y||(Y=!0,x==null||x())}).catch(E=>{E.name!=="AbortError"&&(_==null||_(E.message))}),{abort:()=>w.abort()}}const Qf=(e,t)=>{const n=new Array(e.length+t.length);for(let a=0;a<e.length;a++)n[a]=e[a];for(let a=0;a<t.length;a++)n[e.length+a]=t[a];return n},Zf=(e,t)=>({classGroupId:e,validator:t}),Ed=(e=new Map,t=null,n)=>({nextPart:e,validators:t,classGroupId:n}),ys="-",fl=[],ev="arbitrary..",tv=e=>{const t=nv(e),{conflictingClassGroups:n,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:s=>{if(s.startsWith("[")&&s.endsWith("]"))return rv(s);const l=s.split(ys),u=l[0]===""&&l.length>1?1:0;return Pd(l,u,t)},getConflictingClassGroupIds:(s,l)=>{if(l){const u=a[s],p=n[s];return u?p?Qf(p,u):u:p||fl}return n[s]||fl}}},Pd=(e,t,n)=>{if(e.length-t===0)return n.classGroupId;const o=e[t],i=n.nextPart.get(o);if(i){const p=Pd(e,t+1,i);if(p)return p}const s=n.validators;if(s===null)return;const l=t===0?e.join(ys):e.slice(t).join(ys),u=s.length;for(let p=0;p<u;p++){const x=s[p];if(x.validator(l))return x.classGroupId}},rv=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),n=t.indexOf(":"),a=t.slice(0,n);return a?ev+a:void 0})(),nv=e=>{const{theme:t,classGroups:n}=e;return av(n,t)},av=(e,t)=>{const n=Ed();for(const a in e){const o=e[a];Ei(o,n,a,t)}return n},Ei=(e,t,n,a)=>{const o=e.length;for(let i=0;i<o;i++){const s=e[i];ov(s,t,n,a)}},ov=(e,t,n,a)=>{if(typeof e=="string"){sv(e,t,n);return}if(typeof e=="function"){iv(e,t,n,a);return}lv(e,t,n,a)},sv=(e,t,n)=>{const a=e===""?t:Nd(t,e);a.classGroupId=n},iv=(e,t,n,a)=>{if(dv(e)){Ei(e(a),t,n,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Zf(n,e))},lv=(e,t,n,a)=>{const o=Object.entries(e),i=o.length;for(let s=0;s<i;s++){const[l,u]=o[s];Ei(u,Nd(t,l),n,a)}},Nd=(e,t)=>{let n=e;const a=t.split(ys),o=a.length;for(let i=0;i<o;i++){const s=a[i];let l=n.nextPart.get(s);l||(l=Ed(),n.nextPart.set(s,l)),n=l}return n},dv=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,cv=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,n=Object.create(null),a=Object.create(null);const o=(i,s)=>{n[i]=s,t++,t>e&&(t=0,a=n,n=Object.create(null))};return{get(i){let s=n[i];if(s!==void 0)return s;if((s=a[i])!==void 0)return o(i,s),s},set(i,s){i in n?n[i]=s:o(i,s)}}},pi="!",vl=":",uv=[],pl=(e,t,n,a,o)=>({modifiers:e,hasImportantModifier:t,baseClassName:n,maybePostfixModifierPosition:a,isExternal:o}),fv=e=>{const{prefix:t,experimentalParseClassName:n}=e;let a=o=>{const i=[];let s=0,l=0,u=0,p;const x=o.length;for(let E=0;E<x;E++){const C=o[E];if(s===0&&l===0){if(C===vl){i.push(o.slice(u,E)),u=E+1;continue}if(C==="/"){p=E;continue}}C==="["?s++:C==="]"?s--:C==="("?l++:C===")"&&l--}const _=i.length===0?o:o.slice(u);let y=_,k=!1;_.endsWith(pi)?(y=_.slice(0,-1),k=!0):_.startsWith(pi)&&(y=_.slice(1),k=!0);const w=p&&p>u?p-u:void 0;return pl(i,k,y,w)};if(t){const o=t+vl,i=a;a=s=>s.startsWith(o)?i(s.slice(o.length)):pl(uv,!1,s,void 0,!0)}if(n){const o=a;a=i=>n({className:i,parseClassName:o})}return a},vv=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((n,a)=>{t.set(n,1e6+a)}),n=>{const a=[];let o=[];for(let i=0;i<n.length;i++){const s=n[i],l=s[0]==="[",u=t.has(s);l||u?(o.length>0&&(o.sort(),a.push(...o),o=[]),a.push(s)):o.push(s)}return o.length>0&&(o.sort(),a.push(...o)),a}},pv=e=>({cache:cv(e.cacheSize),parseClassName:fv(e),sortModifiers:vv(e),...tv(e)}),mv=/\s+/,hv=(e,t)=>{const{parseClassName:n,getClassGroupId:a,getConflictingClassGroupIds:o,sortModifiers:i}=t,s=[],l=e.trim().split(mv);let u="";for(let p=l.length-1;p>=0;p-=1){const x=l[p],{isExternal:_,modifiers:y,hasImportantModifier:k,baseClassName:w,maybePostfixModifierPosition:E}=n(x);if(_){u=x+(u.length>0?" "+u:u);continue}let C=!!E,S=a(C?w.substring(0,E):w);if(!S){if(!C){u=x+(u.length>0?" "+u:u);continue}if(S=a(w),!S){u=x+(u.length>0?" "+u:u);continue}C=!1}const R=y.length===0?"":y.length===1?y[0]:i(y).join(":"),Y=k?R+pi:R,T=Y+S;if(s.indexOf(T)>-1)continue;s.push(T);const H=o(S,C);for(let ve=0;ve<H.length;++ve){const se=H[ve];s.push(Y+se)}u=x+(u.length>0?" "+u:u)}return u},xv=(...e)=>{let t=0,n,a,o="";for(;t<e.length;)(n=e[t++])&&(a=Ld(n))&&(o&&(o+=" "),o+=a);return o},Ld=e=>{if(typeof e=="string")return e;let t,n="";for(let a=0;a<e.length;a++)e[a]&&(t=Ld(e[a]))&&(n&&(n+=" "),n+=t);return n},gv=(e,...t)=>{let n,a,o,i;const s=u=>{const p=t.reduce((x,_)=>_(x),e());return n=pv(p),a=n.cache.get,o=n.cache.set,i=l,l(u)},l=u=>{const p=a(u);if(p)return p;const x=hv(u,n);return o(u,x),x};return i=s,(...u)=>i(xv(...u))},bv=[],ir=e=>{const t=n=>n[e]||bv;return t.isThemeGetter=!0,t},Od=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Rd=/^\((?:(\w[\w-]*):)?(.+)\)$/i,_v=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,yv=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,wv=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,kv=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,Cv=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,Sv=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Ca=e=>_v.test(e),He=e=>!!e&&!Number.isNaN(Number(e)),Sa=e=>!!e&&Number.isInteger(Number(e)),Hs=e=>e.endsWith("%")&&He(e.slice(0,-1)),la=e=>yv.test(e),Dd=()=>!0,$v=e=>wv.test(e)&&!kv.test(e),Pi=()=>!1,Mv=e=>Cv.test(e),Iv=e=>Sv.test(e),Tv=e=>!ie(e)&&!de(e),Av=e=>ja(e,Vd,Pi),ie=e=>Od.test(e),Fa=e=>ja(e,qd,$v),ml=e=>ja(e,Dv,He),zv=e=>ja(e,Fd,Dd),Ev=e=>ja(e,Bd,Pi),hl=e=>ja(e,jd,Pi),Pv=e=>ja(e,Wd,Iv),ps=e=>ja(e,Gd,Mv),de=e=>Rd.test(e),Vo=e=>co(e,qd),Nv=e=>co(e,Bd),xl=e=>co(e,jd),Lv=e=>co(e,Vd),Ov=e=>co(e,Wd),ms=e=>co(e,Gd,!0),Rv=e=>co(e,Fd,!0),ja=(e,t,n)=>{const a=Od.exec(e);return a?a[1]?t(a[1]):n(a[2]):!1},co=(e,t,n=!1)=>{const a=Rd.exec(e);return a?a[1]?t(a[1]):n:!1},jd=e=>e==="position"||e==="percentage",Wd=e=>e==="image"||e==="url",Vd=e=>e==="length"||e==="size"||e==="bg-size",qd=e=>e==="length",Dv=e=>e==="number",Bd=e=>e==="family-name",Fd=e=>e==="number"||e==="weight",Gd=e=>e==="shadow",jv=()=>{const e=ir("color"),t=ir("font"),n=ir("text"),a=ir("font-weight"),o=ir("tracking"),i=ir("leading"),s=ir("breakpoint"),l=ir("container"),u=ir("spacing"),p=ir("radius"),x=ir("shadow"),_=ir("inset-shadow"),y=ir("text-shadow"),k=ir("drop-shadow"),w=ir("blur"),E=ir("perspective"),C=ir("aspect"),S=ir("ease"),R=ir("animate"),Y=()=>["auto","avoid","all","avoid-page","page","left","right","column"],T=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],H=()=>[...T(),de,ie],ve=()=>["auto","hidden","clip","visible","scroll"],se=()=>["auto","contain","none"],$=()=>[de,ie,u],ee=()=>[Ca,"full","auto",...$()],ce=()=>[Sa,"none","subgrid",de,ie],re=()=>["auto",{span:["full",Sa,de,ie]},Sa,de,ie],z=()=>[Sa,"auto",de,ie],we=()=>["auto","min","max","fr",de,ie],he=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],ye=()=>["start","end","center","stretch","center-safe","end-safe"],Me=()=>["auto",...$()],ft=()=>[Ca,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...$()],ct=()=>[Ca,"screen","full","dvw","lvw","svw","min","max","fit",...$()],Ce=()=>[Ca,"screen","full","lh","dvh","lvh","svh","min","max","fit",...$()],X=()=>[e,de,ie],et=()=>[...T(),xl,hl,{position:[de,ie]}],At=()=>["no-repeat",{repeat:["","x","y","space","round"]}],N=()=>["auto","cover","contain",Lv,Av,{size:[de,ie]}],oe=()=>[Hs,Vo,Fa],ne=()=>["","none","full",p,de,ie],M=()=>["",He,Vo,Fa],B=()=>["solid","dashed","dotted","double"],pe=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],U=()=>[He,Hs,xl,hl],ae=()=>["","none",w,de,ie],q=()=>["none",He,de,ie],Oe=()=>["none",He,de,ie],We=()=>[He,de,ie],yt=()=>[Ca,"full",...$()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[la],breakpoint:[la],color:[Dd],container:[la],"drop-shadow":[la],ease:["in","out","in-out"],font:[Tv],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[la],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[la],shadow:[la],spacing:["px",He],text:[la],"text-shadow":[la],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Ca,ie,de,C]}],container:["container"],columns:[{columns:[He,ie,de,l]}],"break-after":[{"break-after":Y()}],"break-before":[{"break-before":Y()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:H()}],overflow:[{overflow:ve()}],"overflow-x":[{"overflow-x":ve()}],"overflow-y":[{"overflow-y":ve()}],overscroll:[{overscroll:se()}],"overscroll-x":[{"overscroll-x":se()}],"overscroll-y":[{"overscroll-y":se()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:ee()}],"inset-x":[{"inset-x":ee()}],"inset-y":[{"inset-y":ee()}],start:[{"inset-s":ee(),start:ee()}],end:[{"inset-e":ee(),end:ee()}],"inset-bs":[{"inset-bs":ee()}],"inset-be":[{"inset-be":ee()}],top:[{top:ee()}],right:[{right:ee()}],bottom:[{bottom:ee()}],left:[{left:ee()}],visibility:["visible","invisible","collapse"],z:[{z:[Sa,"auto",de,ie]}],basis:[{basis:[Ca,"full","auto",l,...$()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[He,Ca,"auto","initial","none",ie]}],grow:[{grow:["",He,de,ie]}],shrink:[{shrink:["",He,de,ie]}],order:[{order:[Sa,"first","last","none",de,ie]}],"grid-cols":[{"grid-cols":ce()}],"col-start-end":[{col:re()}],"col-start":[{"col-start":z()}],"col-end":[{"col-end":z()}],"grid-rows":[{"grid-rows":ce()}],"row-start-end":[{row:re()}],"row-start":[{"row-start":z()}],"row-end":[{"row-end":z()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":we()}],"auto-rows":[{"auto-rows":we()}],gap:[{gap:$()}],"gap-x":[{"gap-x":$()}],"gap-y":[{"gap-y":$()}],"justify-content":[{justify:[...he(),"normal"]}],"justify-items":[{"justify-items":[...ye(),"normal"]}],"justify-self":[{"justify-self":["auto",...ye()]}],"align-content":[{content:["normal",...he()]}],"align-items":[{items:[...ye(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...ye(),{baseline:["","last"]}]}],"place-content":[{"place-content":he()}],"place-items":[{"place-items":[...ye(),"baseline"]}],"place-self":[{"place-self":["auto",...ye()]}],p:[{p:$()}],px:[{px:$()}],py:[{py:$()}],ps:[{ps:$()}],pe:[{pe:$()}],pbs:[{pbs:$()}],pbe:[{pbe:$()}],pt:[{pt:$()}],pr:[{pr:$()}],pb:[{pb:$()}],pl:[{pl:$()}],m:[{m:Me()}],mx:[{mx:Me()}],my:[{my:Me()}],ms:[{ms:Me()}],me:[{me:Me()}],mbs:[{mbs:Me()}],mbe:[{mbe:Me()}],mt:[{mt:Me()}],mr:[{mr:Me()}],mb:[{mb:Me()}],ml:[{ml:Me()}],"space-x":[{"space-x":$()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":$()}],"space-y-reverse":["space-y-reverse"],size:[{size:ft()}],"inline-size":[{inline:["auto",...ct()]}],"min-inline-size":[{"min-inline":["auto",...ct()]}],"max-inline-size":[{"max-inline":["none",...ct()]}],"block-size":[{block:["auto",...Ce()]}],"min-block-size":[{"min-block":["auto",...Ce()]}],"max-block-size":[{"max-block":["none",...Ce()]}],w:[{w:[l,"screen",...ft()]}],"min-w":[{"min-w":[l,"screen","none",...ft()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[s]},...ft()]}],h:[{h:["screen","lh",...ft()]}],"min-h":[{"min-h":["screen","lh","none",...ft()]}],"max-h":[{"max-h":["screen","lh",...ft()]}],"font-size":[{text:["base",n,Vo,Fa]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Rv,zv]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",Hs,ie]}],"font-family":[{font:[Nv,Ev,t]}],"font-features":[{"font-features":[ie]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[o,de,ie]}],"line-clamp":[{"line-clamp":[He,"none",de,ml]}],leading:[{leading:[i,...$()]}],"list-image":[{"list-image":["none",de,ie]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",de,ie]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:X()}],"text-color":[{text:X()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...B(),"wavy"]}],"text-decoration-thickness":[{decoration:[He,"from-font","auto",de,Fa]}],"text-decoration-color":[{decoration:X()}],"underline-offset":[{"underline-offset":[He,"auto",de,ie]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:$()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",de,ie]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",de,ie]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:et()}],"bg-repeat":[{bg:At()}],"bg-size":[{bg:N()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},Sa,de,ie],radial:["",de,ie],conic:[Sa,de,ie]},Ov,Pv]}],"bg-color":[{bg:X()}],"gradient-from-pos":[{from:oe()}],"gradient-via-pos":[{via:oe()}],"gradient-to-pos":[{to:oe()}],"gradient-from":[{from:X()}],"gradient-via":[{via:X()}],"gradient-to":[{to:X()}],rounded:[{rounded:ne()}],"rounded-s":[{"rounded-s":ne()}],"rounded-e":[{"rounded-e":ne()}],"rounded-t":[{"rounded-t":ne()}],"rounded-r":[{"rounded-r":ne()}],"rounded-b":[{"rounded-b":ne()}],"rounded-l":[{"rounded-l":ne()}],"rounded-ss":[{"rounded-ss":ne()}],"rounded-se":[{"rounded-se":ne()}],"rounded-ee":[{"rounded-ee":ne()}],"rounded-es":[{"rounded-es":ne()}],"rounded-tl":[{"rounded-tl":ne()}],"rounded-tr":[{"rounded-tr":ne()}],"rounded-br":[{"rounded-br":ne()}],"rounded-bl":[{"rounded-bl":ne()}],"border-w":[{border:M()}],"border-w-x":[{"border-x":M()}],"border-w-y":[{"border-y":M()}],"border-w-s":[{"border-s":M()}],"border-w-e":[{"border-e":M()}],"border-w-bs":[{"border-bs":M()}],"border-w-be":[{"border-be":M()}],"border-w-t":[{"border-t":M()}],"border-w-r":[{"border-r":M()}],"border-w-b":[{"border-b":M()}],"border-w-l":[{"border-l":M()}],"divide-x":[{"divide-x":M()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":M()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...B(),"hidden","none"]}],"divide-style":[{divide:[...B(),"hidden","none"]}],"border-color":[{border:X()}],"border-color-x":[{"border-x":X()}],"border-color-y":[{"border-y":X()}],"border-color-s":[{"border-s":X()}],"border-color-e":[{"border-e":X()}],"border-color-bs":[{"border-bs":X()}],"border-color-be":[{"border-be":X()}],"border-color-t":[{"border-t":X()}],"border-color-r":[{"border-r":X()}],"border-color-b":[{"border-b":X()}],"border-color-l":[{"border-l":X()}],"divide-color":[{divide:X()}],"outline-style":[{outline:[...B(),"none","hidden"]}],"outline-offset":[{"outline-offset":[He,de,ie]}],"outline-w":[{outline:["",He,Vo,Fa]}],"outline-color":[{outline:X()}],shadow:[{shadow:["","none",x,ms,ps]}],"shadow-color":[{shadow:X()}],"inset-shadow":[{"inset-shadow":["none",_,ms,ps]}],"inset-shadow-color":[{"inset-shadow":X()}],"ring-w":[{ring:M()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:X()}],"ring-offset-w":[{"ring-offset":[He,Fa]}],"ring-offset-color":[{"ring-offset":X()}],"inset-ring-w":[{"inset-ring":M()}],"inset-ring-color":[{"inset-ring":X()}],"text-shadow":[{"text-shadow":["none",y,ms,ps]}],"text-shadow-color":[{"text-shadow":X()}],opacity:[{opacity:[He,de,ie]}],"mix-blend":[{"mix-blend":[...pe(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":pe()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[He]}],"mask-image-linear-from-pos":[{"mask-linear-from":U()}],"mask-image-linear-to-pos":[{"mask-linear-to":U()}],"mask-image-linear-from-color":[{"mask-linear-from":X()}],"mask-image-linear-to-color":[{"mask-linear-to":X()}],"mask-image-t-from-pos":[{"mask-t-from":U()}],"mask-image-t-to-pos":[{"mask-t-to":U()}],"mask-image-t-from-color":[{"mask-t-from":X()}],"mask-image-t-to-color":[{"mask-t-to":X()}],"mask-image-r-from-pos":[{"mask-r-from":U()}],"mask-image-r-to-pos":[{"mask-r-to":U()}],"mask-image-r-from-color":[{"mask-r-from":X()}],"mask-image-r-to-color":[{"mask-r-to":X()}],"mask-image-b-from-pos":[{"mask-b-from":U()}],"mask-image-b-to-pos":[{"mask-b-to":U()}],"mask-image-b-from-color":[{"mask-b-from":X()}],"mask-image-b-to-color":[{"mask-b-to":X()}],"mask-image-l-from-pos":[{"mask-l-from":U()}],"mask-image-l-to-pos":[{"mask-l-to":U()}],"mask-image-l-from-color":[{"mask-l-from":X()}],"mask-image-l-to-color":[{"mask-l-to":X()}],"mask-image-x-from-pos":[{"mask-x-from":U()}],"mask-image-x-to-pos":[{"mask-x-to":U()}],"mask-image-x-from-color":[{"mask-x-from":X()}],"mask-image-x-to-color":[{"mask-x-to":X()}],"mask-image-y-from-pos":[{"mask-y-from":U()}],"mask-image-y-to-pos":[{"mask-y-to":U()}],"mask-image-y-from-color":[{"mask-y-from":X()}],"mask-image-y-to-color":[{"mask-y-to":X()}],"mask-image-radial":[{"mask-radial":[de,ie]}],"mask-image-radial-from-pos":[{"mask-radial-from":U()}],"mask-image-radial-to-pos":[{"mask-radial-to":U()}],"mask-image-radial-from-color":[{"mask-radial-from":X()}],"mask-image-radial-to-color":[{"mask-radial-to":X()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":T()}],"mask-image-conic-pos":[{"mask-conic":[He]}],"mask-image-conic-from-pos":[{"mask-conic-from":U()}],"mask-image-conic-to-pos":[{"mask-conic-to":U()}],"mask-image-conic-from-color":[{"mask-conic-from":X()}],"mask-image-conic-to-color":[{"mask-conic-to":X()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:et()}],"mask-repeat":[{mask:At()}],"mask-size":[{mask:N()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",de,ie]}],filter:[{filter:["","none",de,ie]}],blur:[{blur:ae()}],brightness:[{brightness:[He,de,ie]}],contrast:[{contrast:[He,de,ie]}],"drop-shadow":[{"drop-shadow":["","none",k,ms,ps]}],"drop-shadow-color":[{"drop-shadow":X()}],grayscale:[{grayscale:["",He,de,ie]}],"hue-rotate":[{"hue-rotate":[He,de,ie]}],invert:[{invert:["",He,de,ie]}],saturate:[{saturate:[He,de,ie]}],sepia:[{sepia:["",He,de,ie]}],"backdrop-filter":[{"backdrop-filter":["","none",de,ie]}],"backdrop-blur":[{"backdrop-blur":ae()}],"backdrop-brightness":[{"backdrop-brightness":[He,de,ie]}],"backdrop-contrast":[{"backdrop-contrast":[He,de,ie]}],"backdrop-grayscale":[{"backdrop-grayscale":["",He,de,ie]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[He,de,ie]}],"backdrop-invert":[{"backdrop-invert":["",He,de,ie]}],"backdrop-opacity":[{"backdrop-opacity":[He,de,ie]}],"backdrop-saturate":[{"backdrop-saturate":[He,de,ie]}],"backdrop-sepia":[{"backdrop-sepia":["",He,de,ie]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":$()}],"border-spacing-x":[{"border-spacing-x":$()}],"border-spacing-y":[{"border-spacing-y":$()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",de,ie]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[He,"initial",de,ie]}],ease:[{ease:["linear","initial",S,de,ie]}],delay:[{delay:[He,de,ie]}],animate:[{animate:["none",R,de,ie]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[E,de,ie]}],"perspective-origin":[{"perspective-origin":H()}],rotate:[{rotate:q()}],"rotate-x":[{"rotate-x":q()}],"rotate-y":[{"rotate-y":q()}],"rotate-z":[{"rotate-z":q()}],scale:[{scale:Oe()}],"scale-x":[{"scale-x":Oe()}],"scale-y":[{"scale-y":Oe()}],"scale-z":[{"scale-z":Oe()}],"scale-3d":["scale-3d"],skew:[{skew:We()}],"skew-x":[{"skew-x":We()}],"skew-y":[{"skew-y":We()}],transform:[{transform:[de,ie,"","none","gpu","cpu"]}],"transform-origin":[{origin:H()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:yt()}],"translate-x":[{"translate-x":yt()}],"translate-y":[{"translate-y":yt()}],"translate-z":[{"translate-z":yt()}],"translate-none":["translate-none"],accent:[{accent:X()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:X()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",de,ie]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":$()}],"scroll-mx":[{"scroll-mx":$()}],"scroll-my":[{"scroll-my":$()}],"scroll-ms":[{"scroll-ms":$()}],"scroll-me":[{"scroll-me":$()}],"scroll-mbs":[{"scroll-mbs":$()}],"scroll-mbe":[{"scroll-mbe":$()}],"scroll-mt":[{"scroll-mt":$()}],"scroll-mr":[{"scroll-mr":$()}],"scroll-mb":[{"scroll-mb":$()}],"scroll-ml":[{"scroll-ml":$()}],"scroll-p":[{"scroll-p":$()}],"scroll-px":[{"scroll-px":$()}],"scroll-py":[{"scroll-py":$()}],"scroll-ps":[{"scroll-ps":$()}],"scroll-pe":[{"scroll-pe":$()}],"scroll-pbs":[{"scroll-pbs":$()}],"scroll-pbe":[{"scroll-pbe":$()}],"scroll-pt":[{"scroll-pt":$()}],"scroll-pr":[{"scroll-pr":$()}],"scroll-pb":[{"scroll-pb":$()}],"scroll-pl":[{"scroll-pl":$()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",de,ie]}],fill:[{fill:["none",...X()]}],"stroke-w":[{stroke:[He,Vo,Fa,ml]}],stroke:[{stroke:["none",...X()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Wv=gv(jv);function pt(...e){return Wv(Sd(e))}const mi="dartlab-conversations",gl=50;function Vv(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function qv(){try{const e=localStorage.getItem(mi);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const Bv=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function bl(e){return e.map(t=>({...t,messages:t.messages.map(n=>{if(n.role!=="assistant")return n;const a={};for(const[o,i]of Object.entries(n))Bv.includes(o)||(a[o]=i);return a})}))}function _l(e){try{const t={conversations:bl(e.conversations),activeId:e.activeId};localStorage.setItem(mi,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:bl(e.conversations),activeId:e.activeId};localStorage.setItem(mi,JSON.stringify(t))}catch{}}}}function Fv(){const e=qv(),t=e.conversations||[],n=t.find(S=>S.id===e.activeId)?e.activeId:null;let a=G(Tt(t)),o=G(Tt(n)),i=null;function s(){i&&clearTimeout(i),i=setTimeout(()=>{_l({conversations:r(a),activeId:r(o)}),i=null},300)}function l(){i&&clearTimeout(i),i=null,_l({conversations:r(a),activeId:r(o)})}function u(){return r(a).find(S=>S.id===r(o))||null}function p(){const S={id:Vv(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return c(a,[S,...r(a)],!0),r(a).length>gl&&c(a,r(a).slice(0,gl),!0),c(o,S.id,!0),l(),S.id}function x(S){r(a).find(R=>R.id===S)&&(c(o,S,!0),l())}function _(S,R,Y=null){const T=u();if(!T)return;const H={role:S,text:R};Y&&(H.meta=Y),T.messages=[...T.messages,H],T.updatedAt=Date.now(),T.title==="새 대화"&&S==="user"&&(T.title=R.length>30?R.slice(0,30)+"...":R),c(a,[...r(a)],!0),l()}function y(S){const R=u();if(!R||R.messages.length===0)return;const Y=R.messages[R.messages.length-1];Object.assign(Y,S),R.updatedAt=Date.now(),c(a,[...r(a)],!0),s()}function k(S){c(a,r(a).filter(R=>R.id!==S),!0),r(o)===S&&c(o,r(a).length>0?r(a)[0].id:null,!0),l()}function w(){const S=u();!S||S.messages.length===0||(S.messages=S.messages.slice(0,-1),S.updatedAt=Date.now(),c(a,[...r(a)],!0),l())}function E(S,R){const Y=r(a).find(T=>T.id===S);Y&&(Y.title=R,c(a,[...r(a)],!0),l())}function C(){c(a,[],!0),c(o,null),l()}return{get conversations(){return r(a)},get activeId(){return r(o)},get active(){return u()},createConversation:p,setActive:x,addMessage:_,updateLastMessage:y,removeLastMessage:w,deleteConversation:k,updateTitle:E,clearAll:C,flush:l}}const Hd="dartlab-workspace",Gv=6;function Kd(){return typeof window<"u"&&typeof localStorage<"u"}function Hv(){if(!Kd())return{};try{const e=localStorage.getItem(Hd);return e?JSON.parse(e):{}}catch{return{}}}function Kv(e){Kd()&&localStorage.setItem(Hd,JSON.stringify(e))}function vo(e){if(!e)return null;const t=e.stockCode||e.code||null;return t?{stockCode:t,corpName:e.corpName||e.company||t,company:e.company||e.corpName||t,market:e.market||""}:null}function yl(e){const t=vo((e==null?void 0:e.company)||e);return t?{id:t.stockCode,company:t,viewerTopic:(e==null?void 0:e.viewerTopic)||null,viewerTopicLabel:(e==null?void 0:e.viewerTopicLabel)||null,conversationId:(e==null?void 0:e.conversationId)||null,pinned:!!(e!=null&&e.pinned),lastSeenAt:Number.isFinite(e==null?void 0:e.lastSeenAt)?Number(e.lastSeenAt):0}:null}function Uv(){var oe,ne;const e=Hv(),t=Array.isArray(e.workspaceTabs)?e.workspaceTabs.map(yl).filter(Boolean):[],n=vo(e.selectedCompany);t.length===0&&n&&t.push(yl(n));const a=((oe=t.find(M=>M.id===e.activeWorkspaceId))==null?void 0:oe.id)||((ne=t[0])==null?void 0:ne.id)||null,o=t.find(M=>M.id===a)||null;let i=G(!1),s=G(null),l=G(null),u=G("explore"),p=G(null),x=G(null),_=G(Tt((o==null?void 0:o.viewerTopic)||null)),y=G(Tt((o==null?void 0:o.viewerTopicLabel)||null)),k=G(Tt(t)),w=G(Tt(a)),E=G(Tt((o==null?void 0:o.company)||n||null)),C=G(Tt(Array.isArray(e.recentCompanies)?e.recentCompanies.map(vo).filter(Boolean):[]));function S(){Kv({selectedCompany:r(E),recentCompanies:r(C),workspaceTabs:r(k),activeWorkspaceId:r(w)})}function R(M){const B=vo(M);B&&c(C,[B,...r(C).filter(pe=>pe.stockCode!==B.stockCode)].slice(0,Gv),!0)}function Y(){return r(k).find(M=>M.id===r(w))||null}function T(){const M=Y();if(!M){c(E,null),c(_,null),c(y,null);return}c(E,M.company,!0),c(_,M.viewerTopic||null,!0),c(y,M.viewerTopicLabel||M.viewerTopic||null,!0)}function H(M,{activate:B=!0}={}){const pe=vo(M);if(!pe)return null;const U=r(k).findIndex(q=>q.id===pe.stockCode);if(U>=0){const q=r(k)[U],Oe={...q,company:{...q.company,...pe}};return c(k,[...r(k).slice(0,U),Oe,...r(k).slice(U+1)],!0),B&&(c(w,Oe.id,!0),T()),Oe.id}const ae={id:pe.stockCode,company:pe,viewerTopic:null,viewerTopicLabel:null,conversationId:null,pinned:!1,lastSeenAt:0};return c(k,[...r(k),ae],!0),B&&(c(w,ae.id,!0),T()),ae.id}function ve(M){const B=H(M);B&&(R(M),c(s,"viewer"),c(l,null),c(i,!1),ye(B),S())}function se(M){c(s,"data"),c(l,M,!0),c(i,!0),At("explore")}function $(){c(i,!1)}function ee(){c(w,null),c(E,null),c(_,null),c(y,null),c(s,"viewer"),S()}function ce(M){const B=H(M);B&&(R(M),c(s,"viewer"),ye(B),S())}function re(M){r(k).find(B=>B.id===M)&&(c(w,M,!0),c(s,"viewer"),T(),ye(M),S())}function z(M){const B=r(k).findIndex(ae=>ae.id===M);if(B<0)return;const pe=r(w)===M,U=r(k).filter(ae=>ae.id!==M);if(c(k,U,!0),U.length===0)c(w,null),c(E,null),c(_,null),c(y,null);else if(pe){const ae=B>0?B-1:0;c(w,U[Math.min(ae,U.length-1)].id,!0),T()}S()}function we(M,B){M&&(c(k,r(k).map(pe=>pe.id===M?{...pe,conversationId:B||null}:pe),!0),S())}function he(M){M&&(c(k,r(k).map(B=>B.conversationId===M?{...B,conversationId:null}:B),!0),S())}function ye(M,B=Date.now()){if(!M)return;const pe=r(k).find(ae=>ae.id===M),U=Number(B)||0;!pe||U<=(Number(pe.lastSeenAt)||0)||(c(k,r(k).map(ae=>ae.id===M?{...ae,lastSeenAt:U}:ae),!0),S())}function Me(M){const B=r(k).findIndex(q=>q.id===M);if(B<0)return;const pe=r(k)[B],U={...pe,pinned:!pe.pinned};let ae=r(k).filter(q=>q.id!==M);if(U.pinned){const q=ae.findIndex(Oe=>!Oe.pinned);q<0?ae=[...ae,U]:ae=[...ae.slice(0,q),U,...ae.slice(q)]}else{const q=ae.reduce((Oe,We,yt)=>We.pinned?yt:Oe,-1);ae=[...ae.slice(0,q+1),U,...ae.slice(q+1)]}c(k,ae,!0),S()}function ft(M,B){if(!M||!B||M===B)return;const pe=r(k).findIndex(yt=>yt.id===M),U=r(k).findIndex(yt=>yt.id===B);if(pe<0||U<0)return;const ae=r(k)[pe],q=r(k)[U];if(!!ae.pinned!=!!q.pinned)return;const Oe=r(k).filter(yt=>yt.id!==M),We=Oe.findIndex(yt=>yt.id===B);Oe.splice(We,0,ae),c(k,Oe,!0),S()}function ct(M,B){var ae,q,Oe,We;if(!(M!=null&&M.company)&&!(M!=null&&M.stockCode))return;const pe={...r(E)||{},...vo(B)||{},corpName:M.company||((ae=r(E))==null?void 0:ae.corpName)||(B==null?void 0:B.corpName)||(B==null?void 0:B.company),company:M.company||((q=r(E))==null?void 0:q.company)||(B==null?void 0:B.company)||(B==null?void 0:B.corpName),stockCode:M.stockCode||((Oe=r(E))==null?void 0:Oe.stockCode)||(B==null?void 0:B.stockCode),market:((We=r(E))==null?void 0:We.market)||(B==null?void 0:B.market)||""};H(pe)&&(R(pe),S())}function Ce(M,B){c(_,M,!0),c(y,B||M||null,!0),r(w)&&c(k,r(k).map(pe=>pe.id===r(w)?{...pe,viewerTopic:r(_),viewerTopicLabel:r(y)}:pe),!0),S()}function X(M,B=null){c(s,"data"),c(i,!0),c(u,"evidence"),c(p,M,!0),c(x,Number.isInteger(B)?B:null,!0)}function et(){c(p,null),c(x,null)}function At(M){c(u,M||"explore",!0),r(u)!=="evidence"&&et()}function N(){return r(s)==="data"&&r(i)&&r(l)?{type:"data",data:r(l)}:r(E)?{type:"viewer",company:r(E),topic:r(_),topicLabel:r(y)}:null}return{get panelOpen(){return r(i)},get panelMode(){return r(s)},get panelData(){return r(l)},get activeTab(){return r(u)},get activeEvidenceSection(){return r(p)},get selectedEvidenceIndex(){return r(x)},get workspaceTabs(){return r(k)},get activeWorkspaceId(){return r(w)},get activeWorkspace(){return Y()},get selectedCompany(){return r(E)},get recentCompanies(){return r(C)},get viewerTopic(){return r(_)},get viewerTopicLabel(){return r(y)},openViewer:ve,openData:se,openEvidence:X,closePanel:$,clearWorkspaceSelection:ee,selectCompany:ce,selectWorkspace:re,closeWorkspace:z,setWorkspaceConversation:we,clearConversationBinding:he,markWorkspaceSeen:ye,toggleWorkspacePinned:Me,moveWorkspace:ft,setViewerTopic:Ce,clearEvidenceSelection:et,setTab:At,syncCompanyFromMessage:ct,getViewContext:N}}var Yv=g("<a><!></a>"),Xv=g("<button><!></button>");function Jv(e,t){ta(t,!0);let n=Ot(t,"variant",3,"default"),a=Ot(t,"size",3,"default"),o=Wf(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const i={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},s={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=be(),u=Z(l);{var p=_=>{var y=Yv();_s(y,w=>({class:w,...o}),[()=>pt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",i[n()],s[a()],t.class)]);var k=d(y);fi(k,()=>t.children),v(_,y)},x=_=>{var y=Xv();_s(y,w=>({class:w,...o}),[()=>pt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",i[n()],s[a()],t.class)]);var k=d(y);fi(k,()=>t.children),v(_,y)};I(u,_=>{t.href?_(p):_(x,-1)})}v(e,l),ra()}Tu();/**
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
 */const Qv={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Zv=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const wl=(...e)=>e.filter((t,n,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===n).join(" ").trim();var ep=_f("<svg><!><!></svg>");function Le(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]),a=$e(n,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);ta(t,!1);let o=Ot(t,"name",8,void 0),i=Ot(t,"color",8,"currentColor"),s=Ot(t,"size",8,24),l=Ot(t,"strokeWidth",8,2),u=Ot(t,"absoluteStrokeWidth",8,!1),p=Ot(t,"iconNode",24,()=>[]);Rf();var x=ep();_s(x,(k,w,E)=>({...Qv,...k,...a,width:s(),height:s(),stroke:i(),"stroke-width":w,class:E}),[()=>Zv(a)?void 0:{"aria-hidden":"true"},()=>(Ga(u()),Ga(l()),Ga(s()),oo(()=>u()?Number(l())*24/Number(s()):l())),()=>(Ga(wl),Ga(o()),Ga(n),oo(()=>wl("lucide-icon","lucide",o()?`lucide-${o()}`:"",n.class)))]);var _=d(x);ze(_,1,p,Ae,(k,w)=>{var E=F(()=>Pl(r(w),2));let C=()=>r(E)[0],S=()=>r(E)[1];var R=be(),Y=Z(R);If(Y,C,!0,(T,H)=>{_s(T,()=>({...S()}))}),v(k,R)});var y=m(_);Ee(y,t,"default",{}),v(e,x),ra()}function tp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];Le(e,Ne({name:"activity"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function rp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Le(e,Ne({name:"arrow-up"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function kl(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];Le(e,Ne({name:"book-open"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Ks(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Le(e,Ne({name:"brain"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function np(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];Le(e,Ne({name:"chart-column"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function ap(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];Le(e,Ne({name:"check"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function op(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];Le(e,Ne({name:"chevron-down"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function sp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m15 18-6-6 6-6"}]];Le(e,Ne({name:"chevron-left"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Ud(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];Le(e,Ne({name:"chevron-right"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function qo(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Le(e,Ne({name:"circle-alert"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Yo(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Le(e,Ne({name:"circle-check"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function ip(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Le(e,Ne({name:"clock"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function lp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Le(e,Ne({name:"code"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function dp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Le(e,Ne({name:"coffee"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Ha(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Le(e,Ne({name:"database"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function bs(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Le(e,Ne({name:"download"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Cl(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Le(e,Ne({name:"external-link"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function cp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];Le(e,Ne({name:"eye"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Xn(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Le(e,Ne({name:"file-text"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function up(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Le(e,Ne({name:"github"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function fp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["circle",{cx:"9",cy:"12",r:"1"}],["circle",{cx:"9",cy:"5",r:"1"}],["circle",{cx:"9",cy:"19",r:"1"}],["circle",{cx:"15",cy:"12",r:"1"}],["circle",{cx:"15",cy:"5",r:"1"}],["circle",{cx:"15",cy:"19",r:"1"}]];Le(e,Ne({name:"grip-vertical"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Sl(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Le(e,Ne({name:"key"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Kn(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Le(e,Ne({name:"loader-circle"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function vp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Le(e,Ne({name:"log-out"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function pp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];Le(e,Ne({name:"maximize-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function mp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Le(e,Ne({name:"menu"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Xo(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Le(e,Ne({name:"message-square"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function hp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];Le(e,Ne({name:"minimize-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function xp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Le(e,Ne({name:"panel-left-close"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function gp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M15 3v18"}],["path",{d:"m8 9 3 3-3 3"}]];Le(e,Ne({name:"panel-right-close"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function bp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M15 3v18"}],["path",{d:"m10 15-3-3 3-3"}]];Le(e,Ne({name:"panel-right-open"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function $l(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 17v5"}],["path",{d:"M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"}]];Le(e,Ne({name:"pin"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function hi(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Le(e,Ne({name:"plus"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function _p(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Le(e,Ne({name:"refresh-cw"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Jo(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Le(e,Ne({name:"search"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function yp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Le(e,Ne({name:"settings"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function wp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Le(e,Ne({name:"square"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function kp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Le(e,Ne({name:"terminal"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Cp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Le(e,Ne({name:"trash-2"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Sp(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Le(e,Ne({name:"triangle-alert"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Ml(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Le(e,Ne({name:"wrench"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}function Go(e,t){const n=$e(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Le(e,Ne({name:"x"},()=>n,{get iconNode(){return a},children:(o,i)=>{var s=be(),l=Z(s);Ee(l,t,"default",{}),v(o,s)},$$slots:{default:!0}}))}var $p=g("<!> 새 대화",1),Mp=g('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),Ip=g('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),Tp=g('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),Ap=g('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),zp=g('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),Ep=g("<button><!></button>"),Pp=g('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Np=g("<aside><!></aside>");function Lp(e,t){ta(t,!0);let n=Ot(t,"conversations",19,()=>[]),a=Ot(t,"activeId",3,null),o=Ot(t,"open",3,!0),i=Ot(t,"version",3,""),s=G("");function l(w){const E=new Date().setHours(0,0,0,0),C=E-864e5,S=E-7*864e5,R={오늘:[],어제:[],"이번 주":[],이전:[]};for(const T of w)T.updatedAt>=E?R.오늘.push(T):T.updatedAt>=C?R.어제.push(T):T.updatedAt>=S?R["이번 주"].push(T):R.이전.push(T);const Y=[];for(const[T,H]of Object.entries(R))H.length>0&&Y.push({label:T,items:H});return Y}let u=F(()=>r(s).trim()?n().filter(w=>w.title.toLowerCase().includes(r(s).toLowerCase())):n()),p=F(()=>l(r(u)));var x=Np(),_=d(x);{var y=w=>{var E=zp(),C=m(d(E),2),S=d(C);Jv(S,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:(se,$)=>{var ee=$p(),ce=Z(ee);hi(ce,{size:16}),v(se,ee)},$$slots:{default:!0}});var R=m(C,2);{var Y=se=>{var $=Mp(),ee=d($),ce=d(ee);Jo(ce,{size:12,class:"text-dl-text-dim flex-shrink-0"});var re=m(ce,2);mo(re,()=>r(s),z=>c(s,z)),v(se,$)};I(R,se=>{n().length>3&&se(Y)})}var T=m(R,2);ze(T,21,()=>r(p),Ae,(se,$)=>{var ee=Tp(),ce=d(ee),re=d(ce),z=m(ce,2);ze(z,17,()=>r($).items,Ae,(we,he)=>{var ye=Ip(),Me=d(ye),ft=d(Me);Xo(ft,{size:14,class:"flex-shrink-0 opacity-50"});var ct=m(ft,2),Ce=d(ct),X=m(Me,2),et=d(X);Cp(et,{size:12}),O(At=>{ke(ye,1,At),Fr(Me,"aria-current",r(he).id===a()?"true":void 0),L(Ce,r(he).title),Fr(X,"aria-label",`${r(he).title} 삭제`)},[()=>vt(pt("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",r(he).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),Q("click",Me,()=>{var At;return(At=t.onSelect)==null?void 0:At.call(t,r(he).id)}),Q("click",X,At=>{var N;At.stopPropagation(),(N=t.onDelete)==null||N.call(t,r(he).id)}),v(we,ye)}),O(()=>L(re,r($).label)),v(se,ee)});var H=m(T,2);{var ve=se=>{var $=Ap(),ee=d($),ce=d(ee);O(()=>L(ce,`v${i()??""}`)),v(se,$)};I(H,se=>{i()&&se(ve)})}v(w,E)},k=w=>{var E=Pp(),C=m(d(E),2),S=d(C);hi(S,{size:18});var R=m(C,2);ze(R,21,()=>n().slice(0,10),Ae,(Y,T)=>{var H=Ep(),ve=d(H);Xo(ve,{size:16}),O(se=>{ke(H,1,se),Fr(H,"title",r(T).title)},[()=>vt(pt("p-2 rounded-lg transition-colors w-full flex justify-center",r(T).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),Q("click",H,()=>{var se;return(se=t.onSelect)==null?void 0:se.call(t,r(T).id)}),v(Y,H)}),Q("click",C,function(...Y){var T;(T=t.onNewChat)==null||T.apply(this,Y)}),v(w,E)};I(_,w=>{o()?w(y):w(k,-1)})}O(w=>ke(x,1,w),[()=>vt(pt("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",o()?"w-[260px]":"w-[52px]"))]),v(e,x),ra()}lo(["click"]);var Op=g("<span><!></span>");function Bo(e,t){ta(t,!0);let n=Ot(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var o=Op(),i=d(o);fi(i,()=>t.children),O(s=>ke(o,1,s),[()=>vt(pt("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[n()],t.class))]),v(e,o),ra()}function Rp(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function ws(e){if(!e)return"";let t=[],n=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(i,s,l)=>{const u=t.length;return t.push(l.trimEnd()),`
%%CODE_${u}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,i=>{const s=i.trim().split(`
`).filter(y=>y.trim());let l=null,u=-1,p=[];for(let y=0;y<s.length;y++)if(s[y].slice(1,-1).split("|").map(w=>w.trim()).every(w=>/^[\-:]+$/.test(w))){u=y;break}u>0?(l=s[u-1],p=s.slice(u+1)):(u===0||(l=s[0]),p=s.slice(1));let x="<table>";if(l){const y=l.slice(1,-1).split("|").map(k=>k.trim());x+="<thead><tr>"+y.map(k=>`<th>${k.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(p.length>0){x+="<tbody>";for(const y of p){const k=y.slice(1,-1).split("|").map(w=>w.trim());x+="<tr>"+k.map(w=>{let E=w.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Rp(w)?' class="num"':""}>${E}</td>`}).join("")+"</tr>"}x+="</tbody>"}x+="</table>";let _=n.length;return n.push(x),`
%%TABLE_${_}%%
`});let o=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");o=o.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,i=>"<ul>"+i.replace(/<br>/g,"")+"</ul>");for(let i=0;i<n.length;i++)o=o.replace(`%%TABLE_${i}%%`,n[i]);for(let i=0;i<t.length;i++){const s=t[i].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");o=o.replace(`%%CODE_${i}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${s}</code></pre></div>`)}return o=o.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(i,s)=>s.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+o+"</p>"}var Dp=g('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),jp=g('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Wp=g('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),Vp=g('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),qp=g('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Bp=g('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Fp=g('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Gp=g('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Hp=g('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),Kp=g("<button><!> </button>"),Up=g('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Yp=g('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Xp=g('<!> <span class="text-dl-text-dim"> </span>',1),Jp=g('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Qp=g('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Zp=g('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),em=g('<div class="message-committed"><!></div>'),tm=g('<div><div class="message-live-label"> </div> <pre> </pre></div>'),rm=g('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),nm=g('<span class="text-dl-accent/60"> </span>'),am=g('<span class="text-dl-success/60"> </span>'),om=g('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),sm=g('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),im=g('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),lm=g('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),dm=g('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),cm=g("<!>  <div><!> <!></div> <!>",1),um=g('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),fm=g('<span class="text-[10px] text-dl-text-dim"> </span>'),vm=g('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),pm=g("<button> </button>"),mm=g('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),hm=g("<button>시스템 프롬프트</button>"),xm=g("<button>LLM 입력</button>"),gm=g('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),bm=g('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),_m=g('<span class="text-dl-text"> </span>'),ym=g('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),wm=g('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),km=g('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Cm=g("<!> <!>",1);function Sm(e,t){ta(t,!0);let n=G(null),a=G("context"),o=G("raw"),i=F(()=>{var N,oe,ne,M,B,pe;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((N=t.message.toolEvents)==null?void 0:N.length)>0){const U=[...t.message.toolEvents].reverse().find(q=>q.type==="call"),ae=((oe=U==null?void 0:U.arguments)==null?void 0:oe.module)||((ne=U==null?void 0:U.arguments)==null?void 0:ne.keyword)||"";return`도구 실행 중 — ${(U==null?void 0:U.name)||""}${ae?` (${ae})`:""}`}if(((M=t.message.contexts)==null?void 0:M.length)>0){const U=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(U==null?void 0:U.label)||(U==null?void 0:U.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(B=t.message.meta)!=null&&B.company?`${t.message.meta.company} 데이터 검색 중`:(pe=t.message.meta)!=null&&pe.includedModules?"분석 모듈 선택 완료":"생각 중"}),s=F(()=>{var N;return t.message.company||((N=t.message.meta)==null?void 0:N.company)||null});const l={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let u=F(()=>{var N;return(N=t.message.meta)!=null&&N.dialogueMode?l[t.message.meta.dialogueMode]||t.message.meta.dialogueMode:null}),p=F(()=>{var N,oe,ne;return t.message.systemPrompt||t.message.userContent||((N=t.message.contexts)==null?void 0:N.length)>0||((oe=t.message.meta)==null?void 0:oe.includedModules)||((ne=t.message.toolEvents)==null?void 0:ne.length)>0}),x=F(()=>{var oe;const N=(oe=t.message.meta)==null?void 0:oe.dataYearRange;return N?typeof N=="string"?N:N.min_year&&N.max_year?`${N.min_year}~${N.max_year}년`:null:null});function _(N){if(!N)return 0;const oe=(N.match(/[\uac00-\ud7af]/g)||[]).length,ne=N.length-oe;return Math.round(oe*1.5+ne/3.5)}function y(N){return N>=1e3?(N/1e3).toFixed(1)+"k":String(N)}let k=F(()=>{var oe;let N=0;if(t.message.systemPrompt&&(N+=_(t.message.systemPrompt)),t.message.userContent)N+=_(t.message.userContent);else if(((oe=t.message.contexts)==null?void 0:oe.length)>0)for(const ne of t.message.contexts)N+=_(ne.text);return N}),w=F(()=>_(t.message.text)),E=G(void 0);const C=/^\s*\|.+\|\s*$/;function S(N,oe){if(!N)return{committed:"",draft:"",draftType:"none"};if(!oe)return{committed:N,draft:"",draftType:"none"};const ne=N.split(`
`);let M=ne.length;N.endsWith(`
`)||(M=Math.min(M,ne.length-1));let B=0,pe=-1;for(let We=0;We<ne.length;We++)ne[We].trim().startsWith("```")&&(B+=1,pe=We);B%2===1&&pe>=0&&(M=Math.min(M,pe));let U=-1;for(let We=ne.length-1;We>=0;We--){const yt=ne[We];if(!yt.trim())break;if(C.test(yt))U=We;else{U=-1;break}}if(U>=0&&(M=Math.min(M,U)),M<=0)return{committed:"",draft:N,draftType:U===0?"table":B%2===1?"code":"text"};const ae=ne.slice(0,M).join(`
`),q=ne.slice(M).join(`
`);let Oe="text";return q&&U>=M?Oe="table":q&&B%2===1&&(Oe="code"),{committed:ae,draft:q,draftType:Oe}}const R='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',Y='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function T(N){var B;const oe=N.target.closest(".code-copy-btn");if(!oe)return;const ne=oe.closest(".code-block-wrap"),M=((B=ne==null?void 0:ne.querySelector("code"))==null?void 0:B.textContent)||"";navigator.clipboard.writeText(M).then(()=>{oe.innerHTML=Y,setTimeout(()=>{oe.innerHTML=R},2e3)})}function H(N){if(t.onOpenEvidence){t.onOpenEvidence("contexts",N);return}c(n,N,!0),c(a,"context"),c(o,"rendered")}function ve(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}c(n,0),c(a,"system"),c(o,"raw")}function se(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}c(n,0),c(a,"snapshot")}function $(N){var oe;if(t.onOpenEvidence){const ne=(oe=t.message.toolEvents)==null?void 0:oe[N];t.onOpenEvidence((ne==null?void 0:ne.type)==="result"?"tool-results":"tool-calls",N);return}c(n,N,!0),c(a,"tool"),c(o,"raw")}function ee(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}c(n,0),c(a,"userContent"),c(o,"raw")}function ce(){c(n,null)}function re(N){var oe,ne,M,B;return N?N.type==="call"?((oe=N.arguments)==null?void 0:oe.module)||((ne=N.arguments)==null?void 0:ne.keyword)||((M=N.arguments)==null?void 0:M.engine)||((B=N.arguments)==null?void 0:B.name)||"":typeof N.result=="string"?N.result.slice(0,120):N.result&&typeof N.result=="object"&&(N.result.module||N.result.status||N.result.name)||"":""}let z=F(()=>(t.message.toolEvents||[]).filter(N=>N.type==="call")),we=F(()=>(t.message.toolEvents||[]).filter(N=>N.type==="result")),he=F(()=>S(t.message.text||"",t.message.loading)),ye=F(()=>{var oe,ne,M;const N=[];return((ne=(oe=t.message.meta)==null?void 0:oe.includedModules)==null?void 0:ne.length)>0&&N.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:Ha}),((M=t.message.contexts)==null?void 0:M.length)>0&&N.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:cp}),r(z).length>0&&N.push({label:`툴 호출 ${r(z).length}건`,icon:Ml}),r(we).length>0&&N.push({label:`툴 결과 ${r(we).length}건`,icon:Yo}),t.message.systemPrompt&&N.push({label:"시스템 프롬프트",icon:Ks}),t.message.userContent&&N.push({label:"LLM 입력",icon:Xn}),N}),Me=F(()=>{var oe,ne,M;if(!t.message.loading)return[];const N=[];return(oe=t.message.meta)!=null&&oe.company&&N.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&N.push({label:"핵심 수치 확인",done:!0}),(ne=t.message.meta)!=null&&ne.includedModules&&N.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((M=t.message.contexts)==null?void 0:M.length)>0&&N.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&N.push({label:"프롬프트 조립",done:!0}),t.message.text?N.push({label:"응답 작성 중",done:!1}):N.push({label:r(i)||"준비 중",done:!1}),N});var ft=Cm(),ct=Z(ft);{var Ce=N=>{var oe=Dp(),ne=m(d(oe),2),M=d(ne),B=d(M);O(()=>L(B,t.message.text)),v(N,oe)},X=N=>{var oe=um(),ne=m(d(oe),2),M=d(ne);{var B=gt=>{var lt=qp(),bt=d(lt),mr=d(bt);tp(mr,{size:11});var wt=m(bt,4),_t=d(wt);{var zt=De=>{Bo(De,{variant:"muted",children:(Ie,ht)=>{var Te=$a();O(()=>L(Te,r(s))),v(Ie,Te)},$$slots:{default:!0}})};I(_t,De=>{r(s)&&De(zt)})}var b=m(_t,2);{var V=De=>{Bo(De,{variant:"muted",children:(Ie,ht)=>{var Te=$a();O(Qe=>L(Te,Qe),[()=>t.message.meta.market.toUpperCase()]),v(Ie,Te)},$$slots:{default:!0}})};I(b,De=>{var Ie;(Ie=t.message.meta)!=null&&Ie.market&&De(V)})}var D=m(b,2);{var J=De=>{Bo(De,{variant:"accent",children:(Ie,ht)=>{var Te=$a();O(()=>L(Te,r(u))),v(Ie,Te)},$$slots:{default:!0}})};I(D,De=>{r(u)&&De(J)})}var K=m(D,2);{var Ve=De=>{Bo(De,{variant:"muted",children:(Ie,ht)=>{var Te=$a();O(()=>L(Te,t.message.meta.topicLabel)),v(Ie,Te)},$$slots:{default:!0}})};I(K,De=>{var Ie;(Ie=t.message.meta)!=null&&Ie.topicLabel&&De(Ve)})}var qe=m(K,2);{var tr=De=>{Bo(De,{variant:"accent",children:(Ie,ht)=>{var Te=$a();O(()=>L(Te,r(x))),v(Ie,Te)},$$slots:{default:!0}})};I(qe,De=>{r(x)&&De(tr)})}var Je=m(qe,2);{var Ut=De=>{var Ie=be(),ht=Z(Ie);ze(ht,17,()=>t.message.contexts,Ae,(Te,Qe,at)=>{var Ct=jp(),te=d(Ct);Ha(te,{size:10,class:"flex-shrink-0"});var Be=m(te);O(()=>L(Be,` ${(r(Qe).label||r(Qe).module)??""}`)),Q("click",Ct,()=>H(at)),v(Te,Ct)}),v(De,Ie)},rr=De=>{var Ie=Wp(),ht=d(Ie);Ha(ht,{size:10,class:"flex-shrink-0"});var Te=m(ht);O(()=>L(Te,` 모듈 ${t.message.meta.includedModules.length??""}개`)),v(De,Ie)};I(Je,De=>{var Ie,ht,Te;((Ie=t.message.contexts)==null?void 0:Ie.length)>0?De(Ut):((Te=(ht=t.message.meta)==null?void 0:ht.includedModules)==null?void 0:Te.length)>0&&De(rr,1)})}var nr=m(Je,2);ze(nr,17,()=>r(ye),Ae,(De,Ie)=>{var ht=Vp(),Te=d(ht);Mf(Te,()=>r(Ie).icon,(at,Ct)=>{Ct(at,{size:10,class:"flex-shrink-0"})});var Qe=m(Te);O(()=>L(Qe,` ${r(Ie).label??""}`)),Q("click",ht,()=>{r(Ie).label.startsWith("컨텍스트")?H(0):r(Ie).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):$(0):r(Ie).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):$((t.message.toolEvents||[]).findIndex(at=>at.type==="result")):r(Ie).label==="시스템 프롬프트"?ve():r(Ie).label==="LLM 입력"&&ee()}),v(De,ht)}),v(gt,lt)};I(M,gt=>{var lt,bt;(r(s)||r(x)||((lt=t.message.contexts)==null?void 0:lt.length)>0||(bt=t.message.meta)!=null&&bt.includedModules||r(ye).length>0)&&gt(B)})}var pe=m(M,2);{var U=gt=>{var lt=Hp(),bt=d(lt);ze(bt,21,()=>t.message.snapshot.items,Ae,(_t,zt)=>{const b=F(()=>r(zt).status==="good"?"text-dl-success":r(zt).status==="danger"?"text-dl-primary-light":r(zt).status==="caution"?"text-amber-400":"text-dl-text");var V=Bp(),D=d(V),J=d(D),K=m(D,2),Ve=d(K);O(qe=>{L(J,r(zt).label),ke(K,1,qe),L(Ve,r(zt).value)},[()=>vt(pt("text-[14px] font-semibold leading-snug mt-0.5",r(b)))]),v(_t,V)});var mr=m(bt,2);{var wt=_t=>{var zt=Gp();ze(zt,21,()=>t.message.snapshot.warnings,Ae,(b,V)=>{var D=Fp(),J=d(D);Sp(J,{size:10});var K=m(J);O(()=>L(K,` ${r(V)??""}`)),v(b,D)}),v(_t,zt)};I(mr,_t=>{var zt;((zt=t.message.snapshot.warnings)==null?void 0:zt.length)>0&&_t(wt)})}Q("click",lt,se),v(gt,lt)};I(pe,gt=>{var lt,bt;((bt=(lt=t.message.snapshot)==null?void 0:lt.items)==null?void 0:bt.length)>0&&gt(U)})}var ae=m(pe,2);{var q=gt=>{var lt=Up(),bt=d(lt),mr=m(d(bt),4);ze(mr,21,()=>t.message.toolEvents,Ae,(wt,_t,zt)=>{const b=F(()=>re(r(_t)));var V=Kp(),D=d(V);{var J=qe=>{Ml(qe,{size:11})},K=qe=>{Yo(qe,{size:11})};I(D,qe=>{r(_t).type==="call"?qe(J):qe(K,-1)})}var Ve=m(D);O(qe=>{ke(V,1,qe),L(Ve,` ${(r(_t).type==="call"?r(_t).name:`${r(_t).name} 결과`)??""}${r(b)?`: ${r(b)}`:""}`)},[()=>vt(pt("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",r(_t).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),Q("click",V,()=>$(zt)),v(wt,V)}),v(gt,lt)};I(ae,gt=>{var lt;((lt=t.message.toolEvents)==null?void 0:lt.length)>0&&gt(q)})}var Oe=m(ae,2);{var We=gt=>{var lt=Qp(),bt=d(lt);ze(bt,21,()=>r(Me),Ae,(mr,wt)=>{var _t=Jp(),zt=d(_t);{var b=D=>{var J=Yp(),K=m(Z(J),2),Ve=d(K);O(()=>L(Ve,r(wt).label)),v(D,J)},V=D=>{var J=Xp(),K=Z(J);Kn(K,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var Ve=m(K,2),qe=d(Ve);O(()=>L(qe,r(wt).label)),v(D,J)};I(zt,D=>{r(wt).done?D(b):D(V,-1)})}v(mr,_t)}),v(gt,lt)},yt=gt=>{var lt=cm(),bt=Z(lt);{var mr=K=>{var Ve=Zp(),qe=d(Ve);Kn(qe,{size:12,class:"animate-spin flex-shrink-0"});var tr=m(qe,2),Je=d(tr);O(()=>L(Je,r(i))),v(K,Ve)};I(bt,K=>{t.message.loading&&K(mr)})}var wt=m(bt,2),_t=d(wt);{var zt=K=>{var Ve=em(),qe=d(Ve);po(qe,()=>ws(r(he).committed)),v(K,Ve)};I(_t,K=>{r(he).committed&&K(zt)})}var b=m(_t,2);{var V=K=>{var Ve=tm(),qe=d(Ve),tr=d(qe),Je=m(qe,2),Ut=d(Je);O(rr=>{ke(Ve,1,rr),L(tr,r(he).draftType==="table"?"표 구성 중":r(he).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),L(Ut,r(he).draft)},[()=>vt(pt("message-live-tail",r(he).draftType==="table"&&"message-draft-table",r(he).draftType==="code"&&"message-draft-code"))]),v(K,Ve)};I(b,K=>{r(he).draft&&K(V)})}za(wt,K=>c(E,K),()=>r(E));var D=m(wt,2);{var J=K=>{var Ve=dm(),qe=d(Ve);{var tr=Qe=>{var at=rm(),Ct=d(at);ip(Ct,{size:10});var te=m(Ct);O(()=>L(te,` ${t.message.duration??""}초`)),v(Qe,at)};I(qe,Qe=>{t.message.duration&&Qe(tr)})}var Je=m(qe,2);{var Ut=Qe=>{var at=om(),Ct=d(at);{var te=dt=>{var St=nm(),je=d(St);O($t=>L(je,`↑${$t??""}`),[()=>y(r(k))]),v(dt,St)};I(Ct,dt=>{r(k)>0&&dt(te)})}var Be=m(Ct,2);{var ut=dt=>{var St=am(),je=d(St);O($t=>L(je,`↓${$t??""}`),[()=>y(r(w))]),v(dt,St)};I(Be,dt=>{r(w)>0&&dt(ut)})}v(Qe,at)};I(Je,Qe=>{(r(k)>0||r(w)>0)&&Qe(Ut)})}var rr=m(Je,2);{var nr=Qe=>{var at=sm(),Ct=d(at);_p(Ct,{size:10}),Q("click",at,()=>{var te;return(te=t.onRegenerate)==null?void 0:te.call(t)}),v(Qe,at)};I(rr,Qe=>{t.onRegenerate&&Qe(nr)})}var De=m(rr,2);{var Ie=Qe=>{var at=im(),Ct=d(at);Ks(Ct,{size:10}),Q("click",at,ve),v(Qe,at)};I(De,Qe=>{t.message.systemPrompt&&Qe(Ie)})}var ht=m(De,2);{var Te=Qe=>{var at=lm(),Ct=d(at);Xn(Ct,{size:10});var te=m(Ct);O((Be,ut)=>L(te,` LLM 입력 (${Be??""}자 · ~${ut??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>y(_(t.message.userContent))]),Q("click",at,ee),v(Qe,at)};I(ht,Qe=>{t.message.userContent&&Qe(Te)})}v(K,Ve)};I(D,K=>{!t.message.loading&&(t.message.duration||r(p)||t.onRegenerate)&&K(J)})}O(K=>ke(wt,1,K),[()=>vt(pt("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),Q("click",wt,T),v(gt,lt)};I(Oe,gt=>{t.message.loading&&!t.message.text?gt(We):gt(yt,-1)})}v(N,oe)};I(ct,N=>{t.message.role==="user"?N(Ce):N(X,-1)})}var et=m(ct,2);{var At=N=>{const oe=F(()=>r(a)==="system"),ne=F(()=>r(a)==="userContent"),M=F(()=>r(a)==="context"),B=F(()=>r(a)==="snapshot"),pe=F(()=>r(a)==="tool"),U=F(()=>{var te;return r(M)?(te=t.message.contexts)==null?void 0:te[r(n)]:null}),ae=F(()=>{var te;return r(pe)?(te=t.message.toolEvents)==null?void 0:te[r(n)]:null}),q=F(()=>{var te,Be,ut,dt,St;return r(B)?"핵심 수치 (원본 데이터)":r(oe)?"시스템 프롬프트":r(ne)?"LLM에 전달된 입력":r(pe)?((te=r(ae))==null?void 0:te.type)==="call"?`${(Be=r(ae))==null?void 0:Be.name} 호출`:`${(ut=r(ae))==null?void 0:ut.name} 결과`:((dt=r(U))==null?void 0:dt.label)||((St=r(U))==null?void 0:St.module)||""}),Oe=F(()=>{var te;return r(B)?JSON.stringify(t.message.snapshot,null,2):r(oe)?t.message.systemPrompt:r(ne)?t.message.userContent:r(pe)?JSON.stringify(r(ae),null,2):(te=r(U))==null?void 0:te.text});var We=km(),yt=d(We),gt=d(yt),lt=d(gt),bt=d(lt),mr=d(bt);{var wt=te=>{Ha(te,{size:15,class:"text-dl-success flex-shrink-0"})},_t=te=>{Ks(te,{size:15,class:"text-dl-primary-light flex-shrink-0"})},zt=te=>{Xn(te,{size:15,class:"text-dl-accent flex-shrink-0"})},b=te=>{Ha(te,{size:15,class:"flex-shrink-0"})};I(mr,te=>{r(B)?te(wt):r(oe)?te(_t,1):r(ne)?te(zt,2):te(b,-1)})}var V=m(mr,2),D=d(V),J=m(V,2);{var K=te=>{var Be=fm(),ut=d(Be);O(dt=>L(ut,`(${dt??""}자)`),[()=>{var dt,St;return(St=(dt=r(Oe))==null?void 0:dt.length)==null?void 0:St.toLocaleString()}]),v(te,Be)};I(J,te=>{r(oe)&&te(K)})}var Ve=m(bt,2),qe=d(Ve);{var tr=te=>{var Be=vm(),ut=d(Be),dt=d(ut);Xn(dt,{size:11});var St=m(ut,2),je=d(St);lp(je,{size:11}),O(($t,Rt)=>{ke(ut,1,$t),ke(St,1,Rt)},[()=>vt(pt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>vt(pt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",r(o)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),Q("click",ut,()=>c(o,"rendered")),Q("click",St,()=>c(o,"raw")),v(te,Be)};I(qe,te=>{r(M)&&te(tr)})}var Je=m(qe,2),Ut=d(Je);Go(Ut,{size:18});var rr=m(lt,2);{var nr=te=>{var Be=mm(),ut=d(Be);ze(ut,21,()=>t.message.contexts,Ae,(dt,St,je)=>{var $t=pm(),Rt=d($t);O(ar=>{ke($t,1,ar),L(Rt,t.message.contexts[je].label||t.message.contexts[je].module)},[()=>vt(pt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",je===r(n)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),Q("click",$t,()=>{c(n,je,!0)}),v(dt,$t)}),v(te,Be)};I(rr,te=>{var Be;r(M)&&((Be=t.message.contexts)==null?void 0:Be.length)>1&&te(nr)})}var De=m(rr,2);{var Ie=te=>{var Be=gm(),ut=d(Be),dt=d(ut);{var St=Rt=>{var ar=hm();O(fn=>ke(ar,1,fn),[()=>vt(pt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(oe)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),Q("click",ar,()=>{c(a,"system")}),v(Rt,ar)};I(dt,Rt=>{t.message.systemPrompt&&Rt(St)})}var je=m(dt,2);{var $t=Rt=>{var ar=xm();O(fn=>ke(ar,1,fn),[()=>vt(pt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",r(ne)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),Q("click",ar,()=>{c(a,"userContent")}),v(Rt,ar)};I(je,Rt=>{t.message.userContent&&Rt($t)})}v(te,Be)};I(De,te=>{!r(M)&&!r(B)&&!r(pe)&&te(Ie)})}var ht=m(gt,2),Te=d(ht);{var Qe=te=>{var Be=bm(),ut=d(Be);po(ut,()=>{var dt;return ws((dt=r(U))==null?void 0:dt.text)}),v(te,Be)},at=te=>{var Be=ym(),ut=d(Be),dt=m(d(ut),2),St=d(dt),je=m(St);{var $t=Mt=>{var Dn=_m(),Wa=d(Dn);O(Cn=>L(Wa,Cn),[()=>re(r(ae))]),v(Mt,Dn)},Rt=F(()=>re(r(ae)));I(je,Mt=>{r(Rt)&&Mt($t)})}var ar=m(ut,2),fn=d(ar);O(()=>{var Mt;L(St,`${((Mt=r(ae))==null?void 0:Mt.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),L(fn,r(Oe))}),v(te,Be)},Ct=te=>{var Be=wm(),ut=d(Be);O(()=>L(ut,r(Oe))),v(te,Be)};I(Te,te=>{r(M)&&r(o)==="rendered"?te(Qe):r(pe)?te(at,1):te(Ct,-1)})}O(()=>L(D,r(q))),Q("click",We,te=>{te.target===te.currentTarget&&ce()}),Q("keydown",We,te=>{te.key==="Escape"&&ce()}),Q("click",Je,ce),v(N,We)};I(et,N=>{r(n)!==null&&N(At)})}v(e,ft),ra()}lo(["click","keydown"]);var $m=g('<button class="send-btn active"><!></button>'),Mm=g("<button><!></button>"),Im=g('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Tm=g('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Am=g('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),zm=g('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function xi(e,t){ta(t,!0);let n=Ot(t,"inputText",15,""),a=Ot(t,"isLoading",3,!1),o=Ot(t,"large",3,!1),i=Ot(t,"placeholder",3,"메시지를 입력하세요..."),s=G(Tt([])),l=G(!1),u=G(-1),p=null,x=G(void 0);function _($){var ee;if(r(l)&&r(s).length>0){if($.key==="ArrowDown"){$.preventDefault(),c(u,(r(u)+1)%r(s).length);return}if($.key==="ArrowUp"){$.preventDefault(),c(u,r(u)<=0?r(s).length-1:r(u)-1,!0);return}if($.key==="Enter"&&r(u)>=0){$.preventDefault(),w(r(s)[r(u)]);return}if($.key==="Escape"){c(l,!1),c(u,-1);return}}$.key==="Enter"&&!$.shiftKey&&($.preventDefault(),c(l,!1),(ee=t.onSend)==null||ee.call(t))}function y($){$.target.style.height="auto",$.target.style.height=Math.min($.target.scrollHeight,200)+"px"}function k($){y($);const ee=n();p&&clearTimeout(p),ee.length>=2&&!/\s/.test(ee.slice(-1))?p=setTimeout(async()=>{var ce;try{const re=await zd(ee.trim());((ce=re.results)==null?void 0:ce.length)>0?(c(s,re.results.slice(0,6),!0),c(l,!0),c(u,-1)):c(l,!1)}catch{c(l,!1)}},300):c(l,!1)}function w($){var ee;n(`${$.corpName} `),c(l,!1),c(u,-1),(ee=t.onCompanySelect)==null||ee.call(t,$),r(x)&&r(x).focus()}function E(){setTimeout(()=>{c(l,!1)},200)}var C=zm(),S=d(C),R=d(S);za(R,$=>c(x,$),()=>r(x));var Y=m(R,2);{var T=$=>{var ee=$m(),ce=d(ee);wp(ce,{size:14}),Q("click",ee,function(...re){var z;(z=t.onStop)==null||z.apply(this,re)}),v($,ee)},H=$=>{var ee=Mm(),ce=d(ee);{let re=F(()=>o()?18:16);rp(ce,{get size(){return r(re)},strokeWidth:2.5})}O((re,z)=>{ke(ee,1,re),ee.disabled=z},[()=>vt(pt("send-btn",n().trim()&&"active")),()=>!n().trim()]),Q("click",ee,()=>{var re;c(l,!1),(re=t.onSend)==null||re.call(t)}),v($,ee)};I(Y,$=>{a()&&t.onStop?$(T):$(H,-1)})}var ve=m(S,2);{var se=$=>{var ee=Am();ze(ee,21,()=>r(s),Ae,(ce,re,z)=>{var we=Tm(),he=d(we);Jo(he,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var ye=m(he,2),Me=d(ye),ft=d(Me),ct=m(Me,2),Ce=d(ct),X=m(ye,2);{var et=At=>{var N=Im(),oe=d(N);O(()=>L(oe,r(re).sector)),v(At,N)};I(X,At=>{r(re).sector&&At(et)})}O(At=>{ke(we,1,At),L(ft,r(re).corpName),L(Ce,`${r(re).stockCode??""} · ${(r(re).market||"")??""}`)},[()=>vt(pt("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",z===r(u)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),Q("mousedown",we,()=>w(r(re))),qn("mouseenter",we,()=>{c(u,z,!0)}),v(ce,we)}),v($,ee)};I(ve,$=>{r(l)&&r(s).length>0&&$(se)})}O($=>{ke(S,1,$),Fr(R,"placeholder",i())},[()=>vt(pt("input-box",o()&&"large"))]),Q("keydown",R,_),Q("input",R,k),qn("blur",R,E),mo(R,n),v(e,C),ra()}lo(["keydown","input","click","mousedown"]);var Em=g('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Pm=g('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Nm=g('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),Lm=g('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Om(e,t){ta(t,!0);function n(re){if(o())return!1;for(let z=a().length-1;z>=0;z--)if(a()[z].role==="assistant"&&!a()[z].error&&a()[z].text)return z===re;return!1}let a=Ot(t,"messages",19,()=>[]),o=Ot(t,"isLoading",3,!1),i=Ot(t,"inputText",15,""),s=Ot(t,"scrollTrigger",3,0);Ot(t,"selectedCompany",3,null);function l(re){return(z,we)=>{var ye,Me,ft,ct;(ye=t.onOpenEvidence)==null||ye.call(t,z,we);let he;if(z==="contexts")he=(Me=re.contexts)==null?void 0:Me[we];else if(z==="snapshot")he={label:"핵심 수치",module:"snapshot",text:JSON.stringify(re.snapshot,null,2)};else if(z==="system")he={label:"시스템 프롬프트",module:"system",text:re.systemPrompt};else if(z==="input")he={label:"LLM 입력",module:"input",text:re.userContent};else if(z==="tool-calls"||z==="tool-results"){const Ce=(ft=re.toolEvents)==null?void 0:ft[we];he={label:`${(Ce==null?void 0:Ce.name)||"도구"} ${(Ce==null?void 0:Ce.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(Ce,null,2)}}he&&((ct=t.onOpenData)==null||ct.call(t,he))}}let u,p,x=G(!0),_=G(!1),y=G(!0);function k(){if(!u)return;const{scrollTop:re,scrollHeight:z,clientHeight:we}=u;c(y,z-re-we<96),r(y)?(c(x,!0),c(_,!1)):(c(x,!1),c(_,!0))}function w(re="smooth"){p&&(p.scrollIntoView({block:"end",behavior:re}),c(x,!0),c(_,!1))}bn(()=>{s(),!(!u||!p)&&requestAnimationFrame(()=>{!u||!p||(r(x)||r(y)?(p.scrollIntoView({block:"end",behavior:o()?"auto":"smooth"}),c(_,!1)):c(_,!0))})});var E=Lm(),C=d(E),S=d(C),R=d(S);ze(R,17,a,Ae,(re,z,we)=>{{let he=F(()=>n(we)?t.onRegenerate:void 0),ye=F(()=>t.onOpenData?l(r(z)):void 0);Sm(re,{get message(){return r(z)},get onRegenerate(){return r(he)},get onOpenEvidence(){return r(ye)}})}});var Y=m(R,2);za(Y,re=>p=re,()=>p),za(C,re=>u=re,()=>u);var T=m(C,2);{var H=re=>{var z=Em(),we=d(z);Q("click",we,()=>w("smooth")),v(re,z)};I(T,re=>{r(_)&&re(H)})}var ve=m(T,2),se=d(ve),$=d(se);{var ee=re=>{var z=Nm(),we=d(z);{var he=ye=>{var Me=Pm(),ft=d(Me);bs(ft,{size:10}),Q("click",Me,function(...ct){var Ce;(Ce=t.onExport)==null||Ce.apply(this,ct)}),v(ye,Me)};I(we,ye=>{a().length>1&&t.onExport&&ye(he)})}v(re,z)};I($,re=>{o()||re(ee)})}var ce=m($,2);xi(ce,{get isLoading(){return o()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return i()},set inputText(re){i(re)}}),qn("scroll",C,k),v(e,E),ra()}lo(["click"]);var Rm=g('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Dm=g('<div class="text-[11px] text-dl-text-dim"> </div>'),jm=g('<button><!> <span class="truncate flex-1"> </span></button>'),Wm=g('<div class="py-0.5"></div>'),Vm=g('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),qm=g('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Bm=g('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Fm=g('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),Gm=g('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Hm=g('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),Km=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Um=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Ym=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xm=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Jm=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Qm=g('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),Zm=g('<div class="vw-heading-block svelte-1l2nqwu"></div>'),eh=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),th=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),rh=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),nh=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ah=g('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),oh=g('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),sh=g('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),ih=g('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),lh=g('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),dh=g('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),ch=g('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),uh=g('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),fh=g('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),vh=g('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),ph=g('<p class="vw-para"> </p>'),mh=g('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),hh=g('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),xh=g('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),gh=g('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),bh=g('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),_h=g('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),yh=g('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),wh=g('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),kh=g("<th> </th>"),Ch=g("<td> </td>"),Sh=g("<tr></tr>"),$h=g('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Mh=g('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),Ih=g("<th> </th>"),Th=g("<td> </td>"),Ah=g("<tr></tr>"),zh=g('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Eh=g("<button> </button>"),Ph=g('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Nh=g('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),Lh=g('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Oh=g("<th> </th>"),Rh=g("<td> </td>"),Dh=g("<tr></tr>"),jh=g('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Wh=g('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Vh=g('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),qh=g("<tr></tr>"),Bh=g('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Fh=g('<article class="py-6 px-8"><!> <!> <!> <!></article>'),Gh=g('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Hh=g('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),Kh=g('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Uh=g('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Yh(e,t){ta(t,!0);let n=Ot(t,"stockCode",3,null),a=Ot(t,"onTopicChange",3,null),o=G(null),i=G(!1),s=G(Tt(new Set)),l=G(null),u=G(null),p=G(Tt([])),x=G(null),_=G(!1),y=G(Tt([])),k=G(Tt(new Map)),w=new Map,E=G(!1),C=G(Tt(new Map));const S={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},R={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},Y={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function T(b){return Y[b]??99}function H(b){return S[b]||b}function ve(b){return R[b]||b||"기타"}bn(()=>{n()&&se()});async function se(){var b,V;c(i,!0),c(o,null),c(l,null),c(u,null),c(p,[],!0),c(x,null),w=new Map;try{const D=await Xf(n());c(o,D.payload,!0),(b=r(o))!=null&&b.columns&&c(y,r(o).columns.filter(K=>/^\d{4}(Q[1-4])?$/.test(K)),!0);const J=he((V=r(o))==null?void 0:V.rows);J.length>0&&(c(s,new Set([J[0].chapter]),!0),J[0].topics.length>0&&$(J[0].topics[0].topic,J[0].chapter))}catch(D){console.error("viewer load error:",D)}c(i,!1)}async function $(b,V){var D;if(r(l)!==b){if(c(l,b,!0),c(u,V||null,!0),c(k,new Map,!0),c(C,new Map,!0),(D=a())==null||D(b,H(b)),w.has(b)){const J=w.get(b);c(p,J.blocks||[],!0),c(x,J.textDocument||null,!0);return}c(p,[],!0),c(x,null),c(_,!0);try{const J=await Yf(n(),b);c(p,J.blocks||[],!0),c(x,J.textDocument||null,!0),w.set(b,{blocks:r(p),textDocument:r(x)})}catch(J){console.error("topic load error:",J),c(p,[],!0),c(x,null)}c(_,!1)}}function ee(b){const V=new Set(r(s));V.has(b)?V.delete(b):V.add(b),c(s,V,!0)}function ce(b,V){const D=new Map(r(k));D.get(b)===V?D.delete(b):D.set(b,V),c(k,D,!0)}function re(b,V){const D=new Map(r(C));D.set(b,V),c(C,D,!0)}function z(b){return b==="updated"?"최근 수정":b==="new"?"신규":b==="stale"?"과거 유지":"유지"}function we(b){return b==="updated"?"updated":b==="new"?"new":b==="stale"?"stale":"stable"}function he(b){if(!b)return[];const V=new Map,D=new Set;for(const J of b){const K=J.chapter||"";V.has(K)||V.set(K,{chapter:K,topics:[]}),D.has(J.topic)||(D.add(J.topic),V.get(K).topics.push({topic:J.topic,source:J.source||"docs"}))}return[...V.values()].sort((J,K)=>T(J.chapter)-T(K.chapter))}function ye(b){return String(b).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function Me(b){return String(b||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function ft(b){return!b||b.length>88?!1:/^\[.+\]$/.test(b)||/^【.+】$/.test(b)||/^[IVX]+\.\s/.test(b)||/^\d+\.\s/.test(b)||/^[가-힣]\.\s/.test(b)||/^\(\d+\)\s/.test(b)||/^\([가-힣]\)\s/.test(b)}function ct(b){return/^\(\d+\)\s/.test(b)||/^\([가-힣]\)\s/.test(b)?"h5":"h4"}function Ce(b){return/^\[.+\]$/.test(b)||/^【.+】$/.test(b)?"vw-h-bracket":/^\(\d+\)\s/.test(b)||/^\([가-힣]\)\s/.test(b)?"vw-h-sub":"vw-h-section"}function X(b){if(!b)return[];if(/^\|.+\|$/m.test(b)||/^#{1,3} /m.test(b)||/```/.test(b))return[{kind:"markdown",text:b}];const V=[];let D=[];const J=()=>{D.length!==0&&(V.push({kind:"paragraph",text:D.join(" ")}),D=[])};for(const K of String(b).split(`
`)){const Ve=Me(K);if(!Ve){J();continue}if(ft(Ve)){J(),V.push({kind:"heading",text:Ve,tag:ct(Ve),className:Ce(Ve)});continue}D.push(Ve)}return J(),V}function et(b){return b?b.kind==="annual"?`${b.year}Q4`:b.year&&b.quarter?`${b.year}Q${b.quarter}`:b.label||"":""}function At(b){var J;const V=X(b);if(V.length===0)return"";if(((J=V[0])==null?void 0:J.kind)==="markdown")return ws(b);let D="";for(const K of V){if(K.kind==="heading"){D+=`<${K.tag} class="${K.className}">${ye(K.text)}</${K.tag}>`;continue}D+=`<p class="vw-para">${ye(K.text)}</p>`}return D}function N(b){if(!b)return"";const V=b.trim().split(`
`).filter(J=>J.trim());let D="";for(const J of V){const K=J.trim();/^[가-힣]\.\s/.test(K)||/^\d+[-.]/.test(K)?D+=`<h4 class="vw-h-section">${K}</h4>`:/^\(\d+\)\s/.test(K)||/^\([가-힣]\)\s/.test(K)?D+=`<h5 class="vw-h-sub">${K}</h5>`:/^\[.+\]$/.test(K)||/^【.+】$/.test(K)?D+=`<h4 class="vw-h-bracket">${K}</h4>`:D+=`<h5 class="vw-h-sub">${K}</h5>`}return D}function oe(b){var D;const V=r(k).get(b.id);return V&&((D=b==null?void 0:b.views)!=null&&D[V])?b.views[V]:(b==null?void 0:b.latest)||null}function ne(b,V){var J,K;const D=r(k).get(b.id);return D?D===V:((K=(J=b==null?void 0:b.latest)==null?void 0:J.period)==null?void 0:K.label)===V}function M(b){return r(k).has(b.id)}function B(b){return b==="updated"?"변경 있음":b==="new"?"직전 없음":"직전과 동일"}function pe(b){var Ve,qe,tr;if(!b)return[];const V=X(b.body);if(V.length===0||((Ve=V[0])==null?void 0:Ve.kind)==="markdown"||!((qe=b.prevPeriod)!=null&&qe.label)||!((tr=b.diff)!=null&&tr.length))return V;const D=[];for(const Je of b.diff)for(const Ut of Je.paragraphs||[])D.push({kind:Je.kind,text:Me(Ut)});const J=[];let K=0;for(const Je of V){if(Je.kind!=="paragraph"){J.push(Je);continue}for(;K<D.length&&D[K].kind==="removed";)J.push({kind:"removed",text:D[K].text}),K+=1;K<D.length&&["same","added"].includes(D[K].kind)?(J.push({kind:D[K].kind,text:D[K].text||Je.text}),K+=1):J.push({kind:"same",text:Je.text})}for(;K<D.length;)J.push({kind:D[K].kind,text:D[K].text}),K+=1;return J}function U(b){return b==null?!1:/^-?[\d,.]+%?$/.test(String(b).trim().replace(/,/g,""))}function ae(b){return b==null?!1:/^-[\d.]+/.test(String(b).trim().replace(/,/g,""))}function q(b,V){if(b==null||b==="")return"";const D=typeof b=="number"?b:Number(String(b).replace(/,/g,""));if(isNaN(D))return String(b);if(V<=1)return D.toLocaleString("ko-KR");const J=D/V;return Number.isInteger(J)?J.toLocaleString("ko-KR"):J.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function Oe(b){if(b==null||b==="")return"";const V=String(b).trim();if(V.includes(","))return V;const D=V.match(/^(-?\d+)(\.\d+)?(%?)$/);return D?D[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(D[2]||"")+(D[3]||""):V}function We(b){var V,D;return(V=r(o))!=null&&V.rows&&((D=r(o).rows.find(J=>J.topic===b))==null?void 0:D.chapter)||null}function yt(b){const V=b.match(/^(\d{4})(Q([1-4]))?$/);if(!V)return"0000_0";const D=V[1],J=V[3]||"5";return`${D}_${J}`}function gt(b){return[...b].sort((V,D)=>yt(D).localeCompare(yt(V)))}let lt=F(()=>r(p).filter(b=>b.kind!=="text"));var bt=Uh(),mr=d(bt);{var wt=b=>{var V=Rm(),D=d(V);Kn(D,{size:18,class:"animate-spin"}),v(b,V)},_t=b=>{var V=Hh(),D=d(V);{var J=Je=>{var Ut=qm(),rr=d(Ut),nr=d(rr);{var De=ht=>{var Te=Dm(),Qe=d(Te);O(()=>L(Qe,`${r(y).length??""}개 기간 · ${r(y)[0]??""} ~ ${r(y)[r(y).length-1]??""}`)),v(ht,Te)};I(nr,ht=>{r(y).length>0&&ht(De)})}var Ie=m(rr,2);ze(Ie,17,()=>he(r(o).rows),Ae,(ht,Te)=>{var Qe=Vm(),at=d(Qe),Ct=d(at);{var te=Mt=>{op(Mt,{size:11,class:"flex-shrink-0 opacity-40"})},Be=F(()=>r(s).has(r(Te).chapter)),ut=Mt=>{Ud(Mt,{size:11,class:"flex-shrink-0 opacity-40"})};I(Ct,Mt=>{r(Be)?Mt(te):Mt(ut,-1)})}var dt=m(Ct,2),St=d(dt),je=m(dt,2),$t=d(je),Rt=m(at,2);{var ar=Mt=>{var Dn=Wm();ze(Dn,21,()=>r(Te).topics,Ae,(Wa,Cn)=>{var jt=jm(),Ke=d(jt);{var zr=hr=>{np(hr,{size:11,class:"flex-shrink-0 text-blue-400/40"})},na=hr=>{kl(hr,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},vn=hr=>{Xn(hr,{size:11,class:"flex-shrink-0 opacity-30"})};I(Ke,hr=>{r(Cn).source==="finance"?hr(zr):r(Cn).source==="report"?hr(na,1):hr(vn,-1)})}var pa=m(Ke,2),ma=d(pa);O(hr=>{ke(jt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${r(l)===r(Cn).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),L(ma,hr)},[()=>H(r(Cn).topic)]),Q("click",jt,()=>$(r(Cn).topic,r(Te).chapter)),v(Wa,jt)}),v(Mt,Dn)},fn=F(()=>r(s).has(r(Te).chapter));I(Rt,Mt=>{r(fn)&&Mt(ar)})}O(Mt=>{L(St,Mt),L($t,r(Te).topics.length)},[()=>ve(r(Te).chapter)]),Q("click",at,()=>ee(r(Te).chapter)),v(ht,Qe)}),v(Je,Ut)};I(D,Je=>{r(E)||Je(J)})}var K=m(D,2),Ve=d(K);{var qe=Je=>{var Ut=Bm(),rr=d(Ut);Xn(rr,{size:32,strokeWidth:1,class:"opacity-20"}),v(Je,Ut)},tr=Je=>{var Ut=Gh(),rr=Z(Ut),nr=d(rr),De=d(nr);{var Ie=je=>{var $t=Fm(),Rt=d($t);O(ar=>L(Rt,ar),[()=>ve(r(u)||We(r(l)))]),v(je,$t)},ht=F(()=>r(u)||We(r(l)));I(De,je=>{r(ht)&&je(Ie)})}var Te=m(De,2),Qe=d(Te),at=m(nr,2),Ct=d(at);{var te=je=>{hp(je,{size:15})},Be=je=>{pp(je,{size:15})};I(Ct,je=>{r(E)?je(te):je(Be,-1)})}var ut=m(rr,2);{var dt=je=>{var $t=Gm(),Rt=d($t);Kn(Rt,{size:16,class:"animate-spin"}),v(je,$t)},St=je=>{var $t=Fh(),Rt=d($t);{var ar=jt=>{var Ke=Hm();v(jt,Ke)};I(Rt,jt=>{var Ke,zr;r(p).length===0&&!(((zr=(Ke=r(x))==null?void 0:Ke.sections)==null?void 0:zr.length)>0)&&jt(ar)})}var fn=m(Rt,2);{var Mt=jt=>{var Ke=_h(),zr=d(Ke),na=d(zr),vn=d(na);{var pa=ot=>{var xe=Km(),Ue=d(xe);O(st=>L(Ue,`최신 기준 ${st??""}`),[()=>et(r(x).latestPeriod)]),v(ot,xe)};I(vn,ot=>{r(x).latestPeriod&&ot(pa)})}var ma=m(vn,2);{var hr=ot=>{var xe=Um(),Ue=d(xe);O((st,Lt)=>L(Ue,`커버리지 ${st??""}~${Lt??""}`),[()=>et(r(x).firstPeriod),()=>et(r(x).latestPeriod)]),v(ot,xe)};I(ma,ot=>{r(x).firstPeriod&&ot(hr)})}var Va=m(ma,2),Yt=d(Va),Et=m(Va,2);{var xr=ot=>{var xe=Ym(),Ue=d(xe);O(()=>L(Ue,`최근 수정 ${r(x).updatedCount??""}개`)),v(ot,xe)};I(Et,ot=>{r(x).updatedCount>0&&ot(xr)})}var Xt=m(Et,2);{var or=ot=>{var xe=Xm(),Ue=d(xe);O(()=>L(Ue,`신규 ${r(x).newCount??""}개`)),v(ot,xe)};I(Xt,ot=>{r(x).newCount>0&&ot(or)})}var Er=m(Xt,2);{var Pr=ot=>{var xe=Jm(),Ue=d(xe);O(()=>L(Ue,`과거 유지 ${r(x).staleCount??""}개`)),v(ot,xe)};I(Er,ot=>{r(x).staleCount>0&&ot(Pr)})}var Hr=m(zr,2);ze(Hr,17,()=>r(x).sections,Ae,(ot,xe)=>{const Ue=F(()=>oe(r(xe))),st=F(()=>M(r(xe)));var Lt=bh(),gr=d(Lt);{var Pe=Fe=>{var ge=Zm();ze(ge,21,()=>r(xe).headingPath,Ae,(It,Vt)=>{var Nr=Qm(),ur=d(Nr);po(ur,()=>N(r(Vt).text)),v(It,Nr)}),v(Fe,ge)};I(gr,Fe=>{var ge;((ge=r(xe).headingPath)==null?void 0:ge.length)>0&&Fe(Pe)})}var tt=m(gr,2),xt=d(tt),Wt=d(xt),Pt=m(xt,2);{var dr=Fe=>{var ge=eh(),It=d(ge);O(Vt=>L(It,`최신 ${Vt??""}`),[()=>et(r(xe).latestPeriod)]),v(Fe,ge)};I(Pt,Fe=>{var ge;(ge=r(xe).latestPeriod)!=null&&ge.label&&Fe(dr)})}var Kr=m(Pt,2);{var cr=Fe=>{var ge=th(),It=d(ge);O(Vt=>L(It,`최초 ${Vt??""}`),[()=>et(r(xe).firstPeriod)]),v(Fe,ge)};I(Kr,Fe=>{var ge,It;(ge=r(xe).firstPeriod)!=null&&ge.label&&r(xe).firstPeriod.label!==((It=r(xe).latestPeriod)==null?void 0:It.label)&&Fe(cr)})}var Wr=m(Kr,2);{var aa=Fe=>{var ge=rh(),It=d(ge);O(()=>L(It,`${r(xe).periodCount??""}기간`)),v(Fe,ge)};I(Wr,Fe=>{r(xe).periodCount>0&&Fe(aa)})}var ha=m(Wr,2);{var Sn=Fe=>{var ge=nh(),It=d(ge);O(()=>L(It,`최근 변경 ${r(xe).latestChange??""}`)),v(Fe,ge)};I(ha,Fe=>{r(xe).latestChange&&Fe(Sn)})}var oa=m(tt,2);{var zs=Fe=>{var ge=oh();ze(ge,21,()=>r(xe).timeline,Ae,(It,Vt)=>{var Nr=ah(),ur=d(Nr),Lr=d(ur);O((br,_r)=>{ke(Nr,1,`vw-timeline-chip ${br??""}`,"svelte-1l2nqwu"),L(Lr,_r)},[()=>ne(r(xe),r(Vt).period.label)?"is-active":"",()=>et(r(Vt).period)]),Q("click",Nr,()=>ce(r(xe).id,r(Vt).period.label)),v(It,Nr)}),v(Fe,ge)};I(oa,Fe=>{var ge;((ge=r(xe).timeline)==null?void 0:ge.length)>0&&Fe(zs)})}var uo=m(oa,2);{var ss=Fe=>{var ge=lh(),It=d(ge),Vt=d(It),Nr=m(It,2);{var ur=yr=>{var Vr=sh(),qa=d(Vr);O(Bt=>L(qa,`비교 ${Bt??""}`),[()=>et(r(Ue).prevPeriod)]),v(yr,Vr)},Lr=yr=>{var Vr=ih();v(yr,Vr)};I(Nr,yr=>{var Vr;(Vr=r(Ue).prevPeriod)!=null&&Vr.label?yr(ur):yr(Lr,-1)})}var br=m(Nr,2),_r=d(br);O((yr,Vr)=>{L(Vt,`선택 ${yr??""}`),L(_r,Vr)},[()=>et(r(Ue).period),()=>B(r(Ue).status)]),v(Fe,ge)};I(uo,Fe=>{r(st)&&r(Ue)&&Fe(ss)})}var is=m(uo,2);{var Es=Fe=>{const ge=F(()=>r(Ue).digest);var It=vh(),Vt=d(It),Nr=d(Vt),ur=d(Nr),Lr=m(Vt,2),br=d(Lr);ze(br,17,()=>r(ge).items.filter(Bt=>Bt.kind==="numeric"),Ae,(Bt,pn)=>{var Ur=dh(),Ht=m(d(Ur));O(()=>L(Ht,` ${r(pn).text??""}`)),v(Bt,Ur)});var _r=m(br,2);ze(_r,17,()=>r(ge).items.filter(Bt=>Bt.kind==="added"),Ae,(Bt,pn)=>{var Ur=ch(),Ht=m(d(Ur),2),fr=d(Ht);O(()=>L(fr,r(pn).text)),v(Bt,Ur)});var yr=m(_r,2);ze(yr,17,()=>r(ge).items.filter(Bt=>Bt.kind==="removed"),Ae,(Bt,pn)=>{var Ur=uh(),Ht=m(d(Ur),2),fr=d(Ht);O(()=>L(fr,r(pn).text)),v(Bt,Ur)});var Vr=m(yr,2);{var qa=Bt=>{var pn=fh(),Ur=d(pn);O(()=>L(Ur,`외 ${r(ge).wordingCount??""}건 문구 수정`)),v(Bt,pn)};I(Vr,Bt=>{r(ge).wordingCount>0&&Bt(qa)})}O(()=>L(ur,`${r(ge).to??""} vs ${r(ge).from??""}`)),v(Fe,It)};I(is,Fe=>{var ge,It,Vt;r(st)&&((Vt=(It=(ge=r(Ue))==null?void 0:ge.digest)==null?void 0:It.items)==null?void 0:Vt.length)>0&&Fe(Es)})}var Ps=m(is,2);{var Ns=Fe=>{var ge=be(),It=Z(ge);{var Vt=ur=>{var Lr=xh();ze(Lr,21,()=>pe(r(Ue)),Ae,(br,_r)=>{var yr=be(),Vr=Z(yr);{var qa=Ht=>{var fr=be(),jn=Z(fr);po(jn,()=>N(r(_r).text)),v(Ht,fr)},Bt=Ht=>{var fr=ph(),jn=d(fr);O(()=>L(jn,r(_r).text)),v(Ht,fr)},pn=Ht=>{var fr=mh(),jn=d(fr);O(()=>L(jn,r(_r).text)),v(Ht,fr)},Ur=Ht=>{var fr=hh(),jn=d(fr);O(()=>L(jn,r(_r).text)),v(Ht,fr)};I(Vr,Ht=>{r(_r).kind==="heading"?Ht(qa):r(_r).kind==="same"?Ht(Bt,1):r(_r).kind==="added"?Ht(pn,2):r(_r).kind==="removed"&&Ht(Ur,3)})}v(br,yr)}),v(ur,Lr)},Nr=ur=>{var Lr=gh(),br=d(Lr);po(br,()=>At(r(Ue).body)),v(ur,Lr)};I(It,ur=>{var Lr,br;r(st)&&((Lr=r(Ue).prevPeriod)!=null&&Lr.label)&&((br=r(Ue).diff)==null?void 0:br.length)>0?ur(Vt):ur(Nr,-1)})}v(Fe,ge)};I(Ps,Fe=>{r(Ue)&&Fe(Ns)})}O((Fe,ge)=>{ke(Lt,1,`vw-text-section ${r(xe).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),ke(xt,1,`vw-status-pill ${Fe??""}`,"svelte-1l2nqwu"),L(Wt,ge)},[()=>we(r(xe).status),()=>z(r(xe).status)]),v(ot,Lt)}),O(()=>L(Yt,`본문 ${r(x).sectionCount??""}개`)),v(jt,Ke)};I(fn,jt=>{var Ke,zr;((zr=(Ke=r(x))==null?void 0:Ke.sections)==null?void 0:zr.length)>0&&jt(Mt)})}var Dn=m(fn,2);{var Wa=jt=>{var Ke=yh();v(jt,Ke)};I(Dn,jt=>{r(lt).length>0&&jt(Wa)})}var Cn=m(Dn,2);ze(Cn,17,()=>r(lt),Ae,(jt,Ke)=>{var zr=be(),na=Z(zr);{var vn=Yt=>{const Et=F(()=>{var Pe;return((Pe=r(Ke).data)==null?void 0:Pe.columns)||[]}),xr=F(()=>{var Pe;return((Pe=r(Ke).data)==null?void 0:Pe.rows)||[]}),Xt=F(()=>r(Ke).meta||{}),or=F(()=>r(Xt).scaleDivisor||1);var Er=$h(),Pr=Z(Er);{var Hr=Pe=>{var tt=wh(),xt=d(tt);O(()=>L(xt,`(단위: ${r(Xt).scale??""})`)),v(Pe,tt)};I(Pr,Pe=>{r(Xt).scale&&Pe(Hr)})}var ot=m(Pr,2),xe=d(ot),Ue=d(xe),st=d(Ue),Lt=d(st);ze(Lt,21,()=>r(Et),Ae,(Pe,tt,xt)=>{const Wt=F(()=>/^\d{4}/.test(r(tt)));var Pt=kh(),dr=d(Pt);O(()=>{ke(Pt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(Wt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${xt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),L(dr,r(tt))}),v(Pe,Pt)});var gr=m(st);ze(gr,21,()=>r(xr),Ae,(Pe,tt,xt)=>{var Wt=Sh();ke(Wt,1,`hover:bg-white/[0.03] ${xt%2===1?"bg-white/[0.012]":""}`),ze(Wt,21,()=>r(Et),Ae,(Pt,dr,Kr)=>{const cr=F(()=>r(tt)[r(dr)]??""),Wr=F(()=>U(r(cr))),aa=F(()=>ae(r(cr))),ha=F(()=>r(Wr)?q(r(cr),r(or)):r(cr));var Sn=Ch(),oa=d(Sn);O(()=>{ke(Sn,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${r(Wr)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${r(aa)?"text-red-400/60":r(Wr)?"text-dl-text/90":""}
																	${Kr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Kr===0&&xt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),L(oa,r(ha))}),v(Pt,Sn)}),v(Pe,Wt)}),v(Yt,Er)},pa=Yt=>{const Et=F(()=>{var Pe;return((Pe=r(Ke).data)==null?void 0:Pe.columns)||[]}),xr=F(()=>{var Pe;return((Pe=r(Ke).data)==null?void 0:Pe.rows)||[]}),Xt=F(()=>r(Ke).meta||{}),or=F(()=>r(Xt).scaleDivisor||1);var Er=zh(),Pr=Z(Er);{var Hr=Pe=>{var tt=Mh(),xt=d(tt);O(()=>L(xt,`(단위: ${r(Xt).scale??""})`)),v(Pe,tt)};I(Pr,Pe=>{r(Xt).scale&&Pe(Hr)})}var ot=m(Pr,2),xe=d(ot),Ue=d(xe),st=d(Ue),Lt=d(st);ze(Lt,21,()=>r(Et),Ae,(Pe,tt,xt)=>{const Wt=F(()=>/^\d{4}/.test(r(tt)));var Pt=Ih(),dr=d(Pt);O(()=>{ke(Pt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${r(Wt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${xt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),L(dr,r(tt))}),v(Pe,Pt)});var gr=m(st);ze(gr,21,()=>r(xr),Ae,(Pe,tt,xt)=>{var Wt=Ah();ke(Wt,1,`hover:bg-white/[0.03] ${xt%2===1?"bg-white/[0.012]":""}`),ze(Wt,21,()=>r(Et),Ae,(Pt,dr,Kr)=>{const cr=F(()=>r(tt)[r(dr)]??""),Wr=F(()=>U(r(cr))),aa=F(()=>ae(r(cr))),ha=F(()=>r(Wr)?r(or)>1?q(r(cr),r(or)):Oe(r(cr)):r(cr));var Sn=Th(),oa=d(Sn);O(()=>{ke(Sn,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(Wr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(aa)?"text-red-400/60":r(Wr)?"text-dl-text/90":""}
																	${Kr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Kr===0&&xt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),L(oa,r(ha))}),v(Pt,Sn)}),v(Pe,Wt)}),v(Yt,Er)},ma=Yt=>{const Et=F(()=>gt(Object.keys(r(Ke).rawMarkdown))),xr=F(()=>r(C).get(r(Ke).block)??0),Xt=F(()=>r(Et)[r(xr)]||r(Et)[0]);var or=Lh(),Er=d(or);{var Pr=Ue=>{var st=Nh(),Lt=d(st);ze(Lt,17,()=>r(Et).slice(0,8),Ae,(tt,xt,Wt)=>{var Pt=Eh(),dr=d(Pt);O(()=>{ke(Pt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${Wt===r(xr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),L(dr,r(xt))}),Q("click",Pt,()=>re(r(Ke).block,Wt)),v(tt,Pt)});var gr=m(Lt,2);{var Pe=tt=>{var xt=Ph(),Wt=d(xt);O(()=>L(Wt,`외 ${r(Et).length-8}개`)),v(tt,xt)};I(gr,tt=>{r(Et).length>8&&tt(Pe)})}v(Ue,st)};I(Er,Ue=>{r(Et).length>1&&Ue(Pr)})}var Hr=m(Er,2),ot=d(Hr),xe=d(ot);po(xe,()=>ws(r(Ke).rawMarkdown[r(Xt)])),v(Yt,or)},hr=Yt=>{const Et=F(()=>{var st;return((st=r(Ke).data)==null?void 0:st.columns)||[]}),xr=F(()=>{var st;return((st=r(Ke).data)==null?void 0:st.rows)||[]});var Xt=jh(),or=d(Xt),Er=d(or);kl(Er,{size:12,class:"text-emerald-400/50"});var Pr=m(or,2),Hr=d(Pr),ot=d(Hr),xe=d(ot);ze(xe,21,()=>r(Et),Ae,(st,Lt,gr)=>{const Pe=F(()=>/^\d{4}/.test(r(Lt)));var tt=Oh(),xt=d(tt);O(()=>{ke(tt,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${r(Pe)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${gr===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),L(xt,r(Lt))}),v(st,tt)});var Ue=m(ot);ze(Ue,21,()=>r(xr),Ae,(st,Lt,gr)=>{var Pe=Dh();ke(Pe,1,`hover:bg-white/[0.03] ${gr%2===1?"bg-white/[0.012]":""}`),ze(Pe,21,()=>r(Et),Ae,(tt,xt,Wt)=>{const Pt=F(()=>r(Lt)[r(xt)]??""),dr=F(()=>U(r(Pt))),Kr=F(()=>ae(r(Pt)));var cr=Rh(),Wr=d(cr);O(aa=>{ke(cr,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${r(dr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${r(Kr)?"text-red-400/60":r(dr)?"text-dl-text/90":""}
																	${Wt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Wt===0&&gr%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),L(Wr,aa)},[()=>r(dr)?Oe(r(Pt)):r(Pt)]),v(tt,cr)}),v(st,Pe)}),v(Yt,Xt)},Va=Yt=>{const Et=F(()=>r(Ke).data.columns),xr=F(()=>r(Ke).data.rows||[]);var Xt=Bh(),or=d(Xt),Er=d(or),Pr=d(Er),Hr=d(Pr);ze(Hr,21,()=>r(Et),Ae,(xe,Ue)=>{var st=Wh(),Lt=d(st);O(()=>L(Lt,r(Ue))),v(xe,st)});var ot=m(Pr);ze(ot,21,()=>r(xr),Ae,(xe,Ue,st)=>{var Lt=qh();ke(Lt,1,`hover:bg-white/[0.03] ${st%2===1?"bg-white/[0.012]":""}`),ze(Lt,21,()=>r(Et),Ae,(gr,Pe)=>{var tt=Vh(),xt=d(tt);O(()=>L(xt,r(Ue)[r(Pe)]??"")),v(gr,tt)}),v(xe,Lt)}),v(Yt,Xt)};I(na,Yt=>{var Et,xr;r(Ke).kind==="finance"?Yt(vn):r(Ke).kind==="structured"?Yt(pa,1):r(Ke).kind==="raw_markdown"&&r(Ke).rawMarkdown?Yt(ma,2):r(Ke).kind==="report"?Yt(hr,3):((xr=(Et=r(Ke).data)==null?void 0:Et.columns)==null?void 0:xr.length)>0&&Yt(Va,4)})}v(jt,zr)}),v(je,$t)};I(ut,je=>{r(_)?je(dt):je(St,-1)})}O(je=>{L(Qe,je),Fr(at,"title",r(E)?"목차 표시":"전체화면")},[()=>H(r(l))]),Q("click",at,()=>c(E,!r(E))),v(Je,Ut)};I(Ve,Je=>{r(l)?Je(tr,-1):Je(qe)})}v(b,V)},zt=b=>{var V=Kh(),D=d(V);Xn(D,{size:36,strokeWidth:1,class:"opacity-20"}),v(b,V)};I(mr,b=>{var V;r(i)?b(wt):(V=r(o))!=null&&V.rows?b(_t,1):b(zt,-1)})}v(e,bt),ra()}lo(["click"]);var Xh=g('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),Jh=g("<!> <span>확인 중...</span>",1),Qh=g("<!> <span>설정 필요</span>",1),Zh=g('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),ex=g('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),tx=g('<div class="flex items-center px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-dl-text-dim/70"> </div>'),rx=g('<span class="rounded bg-white/5 px-1.5 py-0.5 font-mono text-[9px] text-dl-text-dim/90"> </span>'),nx=g('<span class="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.14em] text-emerald-300"><span class="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400"></span> live</span>'),ax=g('<span class="h-2 w-2 rounded-full bg-dl-primary"></span>'),ox=g('<button class="rounded-lg p-1 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text"><!></button>'),sx=g('<!> <div role="group" draggable="true"><div class="flex flex-col items-center gap-1 px-1 text-dl-text-dim/70"><!> <!></div> <button class="min-w-0 flex-1 rounded-lg px-2 py-1.5 text-left"><div class="flex items-center gap-1.5"><div class="truncate text-[12px] font-semibold text-dl-text"> </div> <!> <!></div> <div class="truncate text-[10px] text-dl-text-dim"> </div> <div class="truncate font-mono text-[10px] text-dl-text-dim/80"> </div></button> <button><!></button> <!></div>',1),ix=g('<div class="px-1 text-[12px] text-dl-text-dim">종목을 검색해 공시 탭을 열어보세요.</div>'),lx=g('<span class="mx-1">·</span> ',1),dx=g('<span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-dl-primary-light">고정 탭</span>'),cx=g('<span class="rounded-full bg-white/5 px-2 py-0.5 font-mono"> </span>'),ux=g('<div class="truncate text-[13px] font-semibold text-dl-text"> </div> <div class="truncate font-mono text-[10px] text-dl-text-dim"> <!></div> <div class="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-dl-text-dim/90"><span class="rounded-full bg-white/5 px-2 py-0.5"> </span> <!> <!></div>',1),fx=g('<div class="text-[13px] font-semibold text-dl-text">전자공시 워크스페이스</div> <div class="text-[11px] text-dl-text-dim">종목별 공시를 탭으로 열고 AI와 함께 탐색합니다.</div>',1),vx=g('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/50 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),px=g('<div class="mt-4 flex flex-wrap justify-center gap-2"></div>'),mx=g('<div class="flex h-full items-center justify-center px-6"><div class="w-full max-w-[560px] text-center"><div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-dl-border/50 bg-dl-bg-card/70 text-dl-text-dim"><!></div> <h1 class="text-2xl font-bold text-dl-text">공시를 메인 캔버스로 읽기</h1> <p class="mt-2 text-sm text-dl-text-muted">종목을 검색하면 탭이 열리고, 현재 보고 있는 섹션을 AI가 그대로 문맥으로 사용합니다.</p> <div class="mx-auto mt-6 max-w-[420px]"><!></div> <!></div></div>'),hx=g('<button class="fixed inset-0 z-20 bg-black/60 backdrop-blur-[1px]" aria-label="우측 패널 닫기"></button>'),xx=g('<button class="mt-4 rounded-xl border border-dl-border/60 bg-dl-bg-card/70 px-3 py-2 text-[11px] font-medium text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light">이 탭에서 새 대화 시작</button>'),gx=g('<div class="flex h-full flex-col items-center justify-center px-6 text-center"><!> <p class="mt-3 text-[13px] font-medium text-dl-text">AI에게 바로 물어보세요</p> <p class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">현재 보고 있는 공시 섹션과 종목 문맥을 그대로 사용합니다.</p> <!> <div class="mt-4 w-full max-w-[320px]"><!></div></div>'),bx=g('<aside><div class="flex h-full min-h-0 flex-col"><div class="flex items-center justify-between border-b border-dl-border/40 px-3 py-2"><div class="flex items-center gap-1 rounded-xl bg-dl-bg-darker/90 p-1"><button><!> <span>AI</span></button> <button><!> <span>데이터</span></button></div> <button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text" aria-label="우측 패널 닫기"><!></button></div> <div class="min-h-0 flex-1"><!></div></div></aside>'),_x=g('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),yx=g('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),wx=g('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),kx=g('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),Cx=g('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),Sx=g('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),$x=g('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),Mx=g('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),Ix=g('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),Tx=g('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),Ax=g('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),zx=g('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),Ex=g('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Px=g('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),Nx=g('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Lx=g('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Ox=g("<button> <!></button>"),Rx=g('<div class="flex flex-wrap gap-1.5"></div>'),Dx=g('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),jx=g('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Wx=g('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Vx=g('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),qx=g('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),Bx=g('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Fx=g('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Gx=g("<!> <!> <!> <!> <!> <!>",1),Hx=g('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Kx=g('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),Ux=g('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Yx=g('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),Xx=g('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Jx=g('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Qx=g('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),Zx=g('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),eg=g('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),tg=g('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),rg=g('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),ng=g('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0 flex-col pt-12"><div class="border-b border-dl-border/40 px-3 pb-3"><div class="flex items-center gap-2"><button class="inline-flex items-center gap-1.5 rounded-xl border border-dl-border/60 bg-dl-bg-card/70 px-3 py-2 text-[11px] font-medium text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"><!> 새 공시 탭</button> <button class="rounded-xl border border-dl-border/60 bg-dl-bg-card/60 p-2 text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light" aria-label="워크스페이스 탭 왼쪽으로 이동"><!></button> <div class="min-w-0 flex-1 overflow-x-auto pb-1"><div class="flex min-w-max items-stretch gap-2"><!> <!></div></div> <button class="rounded-xl border border-dl-border/60 bg-dl-bg-card/60 p-2 text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light" aria-label="워크스페이스 탭 오른쪽으로 이동"><!></button></div></div> <div class="flex flex-1 min-h-0"><main class="min-w-0 flex-1 flex flex-col"><div class="flex items-center justify-between gap-3 border-b border-dl-border/30 px-4 py-2"><div class="min-w-0"><!></div> <div class="flex items-center gap-1"><button><!> <span>AI</span></button> <button><!> <span>데이터</span></button> <button class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text"><!></button></div></div> <div class="min-h-0 flex-1"><!></div></main> <!> <!></div></div></div></div>  <!> <!> <!> <!>',1);function ag(e,t){ta(t,!0);let n=G(""),a=G(!1),o=G(null),i=G(Tt({})),s=G(Tt({})),l=G(null),u=G(null),p=G(Tt([])),x=G(!1),_=G(0),y=G(!0),k=G(""),w=G(!1),E=G(null),C=G(Tt({})),S=G(Tt({})),R=G(""),Y=G(!1),T=G(null),H=G(""),ve=G(!1),se=G(""),$=G(0),ee=G(null),ce=G(null),re=G(null);const z=Uv();let we=G(!0),he=G("chat"),ye=G(null),Me=G(null),ft=G(null),ct=G(!1),Ce=G(""),X=G(Tt([])),et=G(-1),At=null,N=G(null),oe=G(!1);function ne(){const f=window.innerWidth<=768;f&&!r(oe)?(c(x,!1),c(we,!1),z.closePanel()):!f&&r(oe)&&c(we,!0),c(oe,f)}bn(()=>(ne(),window.addEventListener("resize",ne),()=>window.removeEventListener("resize",ne))),bn(()=>{!r(w)||!r(ce)||requestAnimationFrame(()=>{var f;return(f=r(ce))==null?void 0:f.focus()})}),bn(()=>{!r(M)||!r(re)||requestAnimationFrame(()=>{var f;return(f=r(re))==null?void 0:f.focus()})}),bn(()=>{!r(ct)||!r(N)||requestAnimationFrame(()=>{var f;return(f=r(N))==null?void 0:f.focus()})}),bn(()=>{z.panelMode==="data"&&z.panelOpen&&(c(he,"data"),c(we,!0))});let M=G(null),B=G(""),pe=G("error"),U=G(!1);function ae(f,h="error",P=4e3){c(B,f,!0),c(pe,h,!0),c(U,!0),setTimeout(()=>{c(U,!1)},P)}const q=Fv();bn(()=>{mr()});let Oe=G(Tt({}));function We(f){return f==="chatgpt"?"codex":f}function yt(f){return`dartlab-api-key:${We(f)}`}function gt(f){return typeof sessionStorage>"u"||!f?"":sessionStorage.getItem(yt(f))||""}function lt(f,h){typeof sessionStorage>"u"||!f||(h?sessionStorage.setItem(yt(f),h):sessionStorage.removeItem(yt(f)))}async function bt(f,h=null,P=null){var fe;const le=await Gf(f,h,P);if(le!=null&&le.provider){const me=We(le.provider);c(i,{...r(i),[me]:{...r(i)[me]||{},available:!!le.available,model:le.model||((fe=r(i)[me])==null?void 0:fe.model)||h||null}},!0)}return le}async function mr(){var f,h,P;c(y,!0);try{const le=await Ff();c(i,le.providers||{},!0),c(s,le.ollama||{},!0),c(Oe,le.codex||{},!0),le.version&&c(k,le.version,!0);const fe=We(localStorage.getItem("dartlab-provider")),me=localStorage.getItem("dartlab-model"),Se=gt(fe);if(fe&&((f=r(i)[fe])!=null&&f.available)){c(l,fe,!0),c(E,fe,!0),c(R,Se,!0),await wt(fe);const _e=r(C)[fe]||[];me&&_e.includes(me)?c(u,me,!0):_e.length>0&&(c(u,_e[0],!0),localStorage.setItem("dartlab-model",r(u))),c(p,_e,!0),c(y,!1);return}if(fe&&r(i)[fe]){if(c(l,fe,!0),c(E,fe,!0),c(R,Se,!0),Se)try{await bt(fe,me,Se)}catch{}await wt(fe);const _e=r(C)[fe]||[];c(p,_e,!0),me&&_e.includes(me)?c(u,me,!0):_e.length>0&&c(u,_e[0],!0),c(y,!1);return}for(const _e of["codex","ollama","openai"])if((h=r(i)[_e])!=null&&h.available){c(l,_e,!0),c(E,_e,!0),c(R,gt(_e),!0),await wt(_e);const kt=r(C)[_e]||[];c(p,kt,!0),c(u,((P=r(i)[_e])==null?void 0:P.model)||(kt.length>0?kt[0]:null),!0),r(u)&&localStorage.setItem("dartlab-model",r(u));break}}catch{}c(y,!1)}async function wt(f){f=We(f),c(S,{...r(S),[f]:!0},!0);try{const h=await Hf(f);c(C,{...r(C),[f]:h.models||[]},!0)}catch{c(C,{...r(C),[f]:[]},!0)}c(S,{...r(S),[f]:!1},!0)}async function _t(f){var P;f=We(f),c(l,f,!0),c(u,null),c(E,f,!0),localStorage.setItem("dartlab-provider",f),localStorage.removeItem("dartlab-model"),c(R,gt(f),!0),c(T,null),await wt(f);const h=r(C)[f]||[];if(c(p,h,!0),h.length>0&&(c(u,((P=r(i)[f])==null?void 0:P.model)||h[0],!0),localStorage.setItem("dartlab-model",r(u)),r(R)))try{await bt(f,r(u),r(R))}catch{}}async function zt(f){c(u,f,!0),localStorage.setItem("dartlab-model",f);const h=gt(r(l));if(h)try{await bt(We(r(l)),f,h)}catch{}}function b(f){f=We(f),r(E)===f?c(E,null):(c(E,f,!0),wt(f))}async function V(){const f=r(R).trim();if(!(!f||!r(l))){c(Y,!0),c(T,null);try{const h=await bt(We(r(l)),r(u),f);h.available?(lt(r(l),f),c(T,"success"),!r(u)&&h.model&&c(u,h.model,!0),await wt(r(l)),c(p,r(C)[r(l)]||[],!0),ae("API 키 인증 성공","success")):(lt(r(l),""),c(T,"error"))}catch{lt(r(l),""),c(T,"error")}c(Y,!1)}}async function D(){try{await Uf(),r(l)==="codex"&&c(i,{...r(i),codex:{...r(i).codex,available:!1}},!0),ae("Codex 계정 로그아웃 완료","success"),await mr()}catch{ae("로그아웃 실패")}}function J(){const f=r(H).trim();!f||r(ve)||(c(ve,!0),c(se,"준비 중..."),c($,0),c(ee,Kf(f,{onProgress(h){h.total&&h.completed!==void 0?(c($,Math.round(h.completed/h.total*100),!0),c(se,`다운로드 중... ${r($)}%`)):h.status&&c(se,h.status,!0)},async onDone(){c(ve,!1),c(ee,null),c(H,""),c(se,""),c($,0),ae(`${f} 다운로드 완료`,"success"),await wt("ollama"),c(p,r(C).ollama||[],!0),r(p).includes(f)&&await zt(f)},onError(h){c(ve,!1),c(ee,null),c(se,""),c($,0),ae(`다운로드 실패: ${h}`)}}),!0))}function K(){r(ee)&&(r(ee).abort(),c(ee,null)),c(ve,!1),c(H,""),c(se,""),c($,0)}function Ve(){c(x,!r(x))}function qe(){c(he,"chat"),c(we,!0),z.closePanel()}function tr(){c(he,"data"),c(we,!0)}function Je(){c(we,!1),z.closePanel()}function Ut(f){z.openData(f),tr()}function rr(f,h=null){z.openEvidence(f,h),tr()}function nr(f){z.openViewer(f)}function De(f,h,P){const le=(f==null?void 0:f.corpName)||(f==null?void 0:f.company)||(f==null?void 0:f.stockCode)||"선택한 회사",fe=(P==null?void 0:P.label)||(h==null?void 0:h.label)||(h==null?void 0:h.name)||"선택한 데이터";qe(),Mt(`${le}의 ${fe}를 바탕으로 핵심 내용을 분석해줘.`)}function Ie(f){z.selectWorkspace(f);const h=z.workspaceTabs.find(P=>P.id===f);h!=null&&h.conversationId&&q.setActive(h.conversationId)}function ht(f,h){var P;(P=h==null?void 0:h.stopPropagation)==null||P.call(h),z.closeWorkspace(f)}function Te(f,h){var P;(P=h==null?void 0:h.stopPropagation)==null||P.call(h),z.toggleWorkspacePinned(f)}function Qe(f,h){var P;c(ye,f,!0),c(Me,f,!0),(P=h==null?void 0:h.dataTransfer)==null||P.setData("text/plain",f),h!=null&&h.dataTransfer&&(h.dataTransfer.effectAllowed="move")}function at(f,h){var fe;if(!r(ye)||r(ye)===f)return;const P=z.workspaceTabs.find(me=>me.id===r(ye)),le=z.workspaceTabs.find(me=>me.id===f);!P||!le||!!P.pinned!=!!le.pinned||((fe=h==null?void 0:h.preventDefault)==null||fe.call(h),c(Me,f,!0))}function Ct(f,h){var P;if((P=h==null?void 0:h.preventDefault)==null||P.call(h),!r(ye)||r(ye)===f){c(ye,null),c(Me,null);return}z.moveWorkspace(r(ye),f),c(ye,null),c(Me,null)}function te(){c(ye,null),c(Me,null)}function Be(f){var h,P;(P=(h=r(ft))==null?void 0:h.scrollBy)==null||P.call(h,{left:f,behavior:"smooth"})}function ut(){if(c(R,""),c(T,null),r(l))c(E,r(l),!0);else{const f=Object.keys(r(i));c(E,f.length>0?f[0]:null,!0)}c(w,!0),r(E)&&wt(r(E))}function dt(f){const h=St(f);return h?(z.syncCompanyFromMessage(h,z.selectedCompany),h):null}function St(f){var h,P,le,fe,me;if(!f)return null;for(let Se=f.messages.length-1;Se>=0;Se--){const _e=f.messages[Se];if(_e.role==="assistant"&&((h=_e.meta)!=null&&h.stockCode||(P=_e.meta)!=null&&P.company||_e.company))return{company:((le=_e.meta)==null?void 0:le.company)||_e.company,stockCode:(fe=_e.meta)==null?void 0:fe.stockCode,market:((me=_e.meta)==null?void 0:me.market)||""}}return null}function je(){q.createConversation(),z.activeWorkspaceId&&z.setWorkspaceConversation(z.activeWorkspaceId,q.activeId),c(n,""),c(a,!1),r(o)&&(r(o).abort(),c(o,null))}function $t(f){q.setActive(f);const h=q.active,P=dt(h);P!=null&&P.stockCode?(z.openViewer(P),z.setWorkspaceConversation(P.stockCode,f)):z.clearWorkspaceSelection(),c(n,""),c(a,!1),r(o)&&(r(o).abort(),c(o,null))}function Rt(f){c(M,f,!0)}function ar(){r(M)&&(z.clearConversationBinding(r(M)),q.deleteConversation(r(M)),c(M,null))}function fn(){var h;const f=q.active;if(!f)return null;for(let P=f.messages.length-1;P>=0;P--){const le=f.messages[P];if(le.role==="assistant"&&((h=le.meta)!=null&&h.stockCode))return le.meta.stockCode}return null}async function Mt(f=null){var Dr,wr,Yr;const h=(f??r(n)).trim();if(!h||r(a))return;if(!r(l)||!((Dr=r(i)[r(l)])!=null&&Dr.available)){ae("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),ut();return}let P=r(na);if(z.activeWorkspaceId?P?q.activeId!==P&&q.setActive(P):(P=q.createConversation(),z.setWorkspaceConversation(z.activeWorkspaceId,P)):q.activeId?P=q.activeId:P=q.createConversation(),!P)return;q.activeId!==P&&q.setActive(P),q.addMessage("user",h),c(n,""),c(a,!0),q.addMessage("assistant",""),q.updateLastMessage({loading:!0,startedAt:Date.now()}),Ko(_);const le=q.active,fe=[];let me=null;if(le){const W=le.messages.slice(0,-2);for(const j of W)if((j.role==="user"||j.role==="assistant")&&j.text&&j.text.trim()&&!j.error&&!j.loading){const ue={role:j.role,text:j.text};j.role==="assistant"&&((wr=j.meta)!=null&&wr.stockCode)&&(ue.meta={company:j.meta.company||j.company,stockCode:j.meta.stockCode,modules:j.meta.includedModules||null,market:j.meta.market||null,topic:j.meta.topic||null,topicLabel:j.meta.topicLabel||null,dialogueMode:j.meta.dialogueMode||null,questionTypes:j.meta.questionTypes||null,userGoal:j.meta.userGoal||null},me=j.meta.stockCode),fe.push(ue)}}const Se=((Yr=z.selectedCompany)==null?void 0:Yr.stockCode)||me||fn(),_e=z.getViewContext();function kt(){return q.activeId!==P}const Ft={provider:r(l),model:r(u),viewContext:_e},Or=gt(r(l));Or&&(Ft.api_key=Or);const Rr=Jf(Se,h,Ft,{onMeta(W){var qt;if(kt())return;const j=q.active,ue=j==null?void 0:j.messages[j.messages.length-1],Ge={meta:{...(ue==null?void 0:ue.meta)||{},...W}};W.company&&(Ge.company=W.company,q.activeId&&((qt=q.active)==null?void 0:qt.title)==="새 대화"&&q.updateTitle(q.activeId,W.company)),W.stockCode&&(Ge.stockCode=W.stockCode),(W.company||W.stockCode)&&z.syncCompanyFromMessage(W,z.selectedCompany),q.updateLastMessage(Ge)},onSnapshot(W){kt()||q.updateLastMessage({snapshot:W})},onContext(W){if(kt())return;const j=q.active;if(!j)return;const ue=j.messages[j.messages.length-1],Re=(ue==null?void 0:ue.contexts)||[];q.updateLastMessage({contexts:[...Re,{module:W.module,label:W.label,text:W.text}]})},onSystemPrompt(W){kt()||q.updateLastMessage({systemPrompt:W.text,userContent:W.userContent||null})},onToolCall(W){if(kt())return;const j=q.active;if(!j)return;const ue=j.messages[j.messages.length-1],Re=(ue==null?void 0:ue.toolEvents)||[];q.updateLastMessage({toolEvents:[...Re,{type:"call",name:W.name,arguments:W.arguments}]})},onToolResult(W){if(kt())return;const j=q.active;if(!j)return;const ue=j.messages[j.messages.length-1],Re=(ue==null?void 0:ue.toolEvents)||[];q.updateLastMessage({toolEvents:[...Re,{type:"result",name:W.name,result:W.result}]})},onChunk(W){if(kt())return;const j=q.active;if(!j)return;const ue=j.messages[j.messages.length-1];q.updateLastMessage({text:((ue==null?void 0:ue.text)||"")+W}),Ko(_)},onDone(){if(kt())return;const W=q.active,j=W==null?void 0:W.messages[W.messages.length-1],ue=j!=null&&j.startedAt?((Date.now()-j.startedAt)/1e3).toFixed(1):null;q.updateLastMessage({loading:!1,duration:ue}),q.flush(),c(a,!1),c(o,null),Ko(_)},onError(W,j,ue){kt()||(q.updateLastMessage({text:`오류: ${W}`,loading:!1,error:!0}),q.flush(),j==="login"?(ae(`${W} — 설정에서 Codex 로그인을 확인하세요`),ut()):j==="install"?(ae(`${W} — 설정에서 Codex 설치 안내를 확인하세요`),ut()):ae(W),c(a,!1),c(o,null))}},fe);c(o,Rr,!0)}function Dn(){r(o)&&(r(o).abort(),c(o,null),c(a,!1),q.updateLastMessage({loading:!1}),q.flush())}function Wa(){const f=q.active;if(!f||f.messages.length<2)return;let h="";for(let P=f.messages.length-1;P>=0;P--)if(f.messages[P].role==="user"){h=f.messages[P].text;break}h&&(q.removeLastMessage(),q.removeLastMessage(),c(n,h,!0),requestAnimationFrame(()=>{Mt()}))}function Cn(){const f=q.active;if(!f)return;let h=`# ${f.title}

`;for(const me of f.messages)me.role==="user"?h+=`## You

${me.text}

`:me.role==="assistant"&&me.text&&(h+=`## DartLab

${me.text}

`);const P=new Blob([h],{type:"text/markdown;charset=utf-8"}),le=URL.createObjectURL(P),fe=document.createElement("a");fe.href=le,fe.download=`${f.title||"dartlab-chat"}.md`,fe.click(),URL.revokeObjectURL(le),ae("대화가 마크다운으로 내보내졌습니다","success")}function jt(){c(ct,!0),c(Ce,""),c(X,[],!0),c(et,-1)}function Ke(f){if((f.metaKey||f.ctrlKey)&&f.key==="n"&&(f.preventDefault(),je()),(f.metaKey||f.ctrlKey)&&/^[1-9]$/.test(f.key)){const h=Number(f.key)-1,P=z.workspaceTabs[h];P&&(f.preventDefault(),Ie(P.id))}(f.metaKey||f.ctrlKey)&&f.key==="k"&&(f.preventDefault(),jt()),(f.metaKey||f.ctrlKey)&&f.shiftKey&&f.key==="S"&&(f.preventDefault(),Ve()),f.key==="Escape"&&r(ct)?c(ct,!1):f.key==="Escape"&&r(w)?c(w,!1):f.key==="Escape"&&r(M)?c(M,null):f.key==="Escape"&&(z.panelOpen||r(we))&&Je()}let zr=F(()=>new Map(q.conversations.map(f=>[f.id,f]))),na=F(()=>z.activeWorkspace?z.activeWorkspace.conversationId||null:q.activeId),vn=F(()=>r(na)&&r(zr).get(r(na))||null),pa=F(()=>{var f;return((f=r(vn))==null?void 0:f.messages)||[]}),ma=F(()=>r(vn)&&r(vn).messages.length>0),hr=F(()=>[...r(pa)].reverse().find(f=>(f==null?void 0:f.role)==="assistant"&&(f.contexts&&f.contexts.length>0||f.snapshot||f.systemPrompt||f.userContent||f.toolEvents&&f.toolEvents.length>0))||null),Va=F(()=>{var f;return!r(y)&&(!r(l)||!((f=r(i)[r(l)])!=null&&f.available))});function Yt(f){return f!=null&&f.conversationId&&r(zr).get(f.conversationId)||null}function Et(f){var le;const h=Yt(f);if(!h||h.id!==q.activeId)return!1;const P=(le=h.messages)==null?void 0:le[h.messages.length-1];return!!(r(a)&&(P==null?void 0:P.role)==="assistant"&&(P!=null&&P.loading))}function xr(f){if(!f||f.id===z.activeWorkspaceId)return!1;const h=Yt(f);return h!=null&&h.updatedAt?h.updatedAt>(f.lastSeenAt||0):!1}function Xt(f){return(f==null?void 0:f.viewerTopicLabel)||(f==null?void 0:f.viewerTopic)||"섹션 미선택"}function or(f){if(!(f!=null&&f.id))return null;const h=z.workspaceTabs.findIndex(P=>P.id===f.id);return h>=0&&h<9?String(h+1):null}function Er(){var f,h;return z.activeWorkspace?(h=r(vn))!=null&&h.title?r(vn).title:"연결된 대화 없음":((f=q.active)==null?void 0:f.title)||"일반 대화"}bn(()=>{const f=z.activeWorkspace,h=q.active;!(f!=null&&f.id)||!(h!=null&&h.id)||f.conversationId===h.id&&z.markWorkspaceSeen(f.id,h.updatedAt||Date.now())}),bn(()=>{const f=z.activeWorkspaceId,h=r(ft);!f||!h||requestAnimationFrame(()=>{var fe;const P=`[data-workspace-tab="${f}"]`,le=h.querySelector(P);(fe=le==null?void 0:le.scrollIntoView)==null||fe.call(le,{inline:"center",block:"nearest",behavior:"smooth"})})});const Pr=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var Hr=ng();qn("keydown",ii,Ke);var ot=Z(Hr),xe=d(ot);{var Ue=f=>{var h=Xh();Q("click",h,()=>{c(x,!1)}),v(f,h)};I(xe,f=>{r(oe)&&r(x)&&f(Ue)})}var st=m(xe,2),Lt=d(st);{let f=F(()=>r(oe)?!0:r(x));Lp(Lt,{get conversations(){return q.conversations},get activeId(){return q.activeId},get open(){return r(f)},get version(){return r(k)},onNewChat:()=>{je(),r(oe)&&c(x,!1)},onSelect:h=>{$t(h),r(oe)&&c(x,!1)},onDelete:Rt,onOpenSearch:jt})}var gr=m(st,2),Pe=d(gr),tt=d(Pe),xt=d(tt);{var Wt=f=>{xp(f,{size:18})},Pt=f=>{mp(f,{size:18})};I(xt,f=>{r(x)?f(Wt):f(Pt,-1)})}var dr=m(Pe,2),Kr=d(dr),cr=d(Kr);Jo(cr,{size:14});var Wr=m(Kr,2),aa=d(Wr);Xn(aa,{size:14});var ha=m(Wr,2),Sn=d(ha);up(Sn,{size:14});var oa=m(ha,2),zs=d(oa);dp(zs,{size:14});var uo=m(oa,2),ss=d(uo);{var is=f=>{var h=Jh(),P=Z(h);Kn(P,{size:12,class:"animate-spin"}),v(f,h)},Es=f=>{var h=Qh(),P=Z(h);qo(P,{size:12}),v(f,h)},Ps=f=>{var h=ex(),P=m(Z(h),2),le=d(P),fe=m(P,2);{var me=Se=>{var _e=Zh(),kt=m(Z(_e),2),Ft=d(kt);O(()=>L(Ft,r(u))),v(Se,_e)};I(fe,Se=>{r(u)&&Se(me)})}O(()=>L(le,r(l))),v(f,h)};I(ss,f=>{r(y)?f(is):r(Va)?f(Es,1):f(Ps,-1)})}var Ns=m(ss,2);yp(Ns,{size:12});var Fe=m(dr,2),ge=d(Fe),It=d(ge),Vt=d(It),Nr=d(Vt);hi(Nr,{size:12});var ur=m(Vt,2),Lr=d(ur);sp(Lr,{size:13});var br=m(ur,2),_r=d(br),yr=d(_r);ze(yr,17,()=>z.workspaceTabs,Ae,(f,h,P)=>{var le=sx(),fe=Z(le);{var me=Ze=>{var Zt=tx(),sa=d(Zt);O(()=>L(sa,r(h).pinned?"고정":"탭")),v(Ze,Zt)};I(fe,Ze=>{(P===0||z.workspaceTabs[P-1].pinned!==r(h).pinned)&&Ze(me)})}var Se=m(fe,2),_e=d(Se),kt=d(_e);fp(kt,{size:12});var Ft=m(kt,2);{var Or=Ze=>{$l(Ze,{size:11,class:"text-dl-primary-light"})};I(Ft,Ze=>{r(h).pinned&&Ze(Or)})}var Rr=m(_e,2),Dr=d(Rr),wr=d(Dr),Yr=d(wr),W=m(wr,2);{var j=Ze=>{var Zt=rx(),sa=d(Zt);O(Po=>L(sa,Po),[()=>or(r(h))]),v(Ze,Zt)},ue=F(()=>or(r(h)));I(W,Ze=>{r(ue)&&Ze(j)})}var Re=m(W,2);{var Ge=Ze=>{var Zt=nx();v(Ze,Zt)},qt=F(()=>Et(r(h))),Jt=Ze=>{var Zt=ax();v(Ze,Zt)},kr=F(()=>xr(r(h)));I(Re,Ze=>{r(qt)?Ze(Ge):r(kr)&&Ze(Jt,1)})}var Xr=m(Dr,2),nn=d(Xr),mn=m(Xr,2),$n=d(mn),Qt=m(Rr,2),Mn=d(Qt);$l(Mn,{size:12});var xa=m(Qt,2);{var ga=Ze=>{var Zt=ox(),sa=d(Zt);Go(sa,{size:12}),O(()=>Fr(Zt,"aria-label",`${r(h).company.corpName} 탭 닫기`)),Q("click",Zt,Po=>ht(r(h).id,Po)),v(Ze,Zt)};I(xa,Ze=>{z.workspaceTabs.length>1&&Ze(ga)})}O((Ze,Zt,sa)=>{ke(Se,1,Ze),Fr(Se,"data-workspace-tab",r(h).id),Fr(Se,"data-workspace-pinned",r(h).pinned?"true":"false"),Fr(Se,"aria-label",`${r(h).company.corpName} 워크스페이스 탭`),L(Yr,r(h).company.corpName),L(nn,Zt),L($n,r(h).company.stockCode),ke(Qt,1,sa),Fr(Qt,"aria-label",r(h).pinned?`${r(h).company.corpName} 탭 고정 해제`:`${r(h).company.corpName} 탭 고정`),Fr(Qt,"title",r(h).pinned?"고정 해제":"상단 고정")},[()=>vt(pt("flex min-w-0 max-w-[260px] items-center gap-1 rounded-xl border px-1 py-1 transition-colors",z.activeWorkspaceId===r(h).id?"border-dl-primary/30 bg-dl-primary/10":"border-dl-border/50 bg-dl-bg-card/50 hover:border-dl-border hover:bg-dl-bg-card/80",r(Me)===r(h).id&&r(ye)!==r(h).id&&"ring-1 ring-dl-primary/40")),()=>Xt(r(h)),()=>vt(pt("rounded-lg p-1 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text",r(h).pinned&&"text-dl-primary-light"))]),qn("dragstart",Se,Ze=>Qe(r(h).id,Ze)),qn("dragover",Se,Ze=>at(r(h).id,Ze)),qn("drop",Se,Ze=>Ct(r(h).id,Ze)),qn("dragend",Se,te),Q("click",Rr,()=>Ie(r(h).id)),Q("click",Qt,Ze=>Te(r(h).id,Ze)),v(f,le)});var Vr=m(yr,2);{var qa=f=>{var h=ix();v(f,h)};I(Vr,f=>{z.workspaceTabs.length===0&&f(qa)})}za(br,f=>c(ft,f),()=>r(ft));var Bt=m(br,2),pn=d(Bt);Ud(pn,{size:13});var Ur=m(ge,2),Ht=d(Ur),fr=d(Ht),jn=d(fr),Yd=d(jn);{var Xd=f=>{var h=ux(),P=Z(h),le=d(P),fe=m(P,2),me=d(fe),Se=m(me);{var _e=j=>{var ue=lx(),Re=m(Z(ue),1,!0);O(()=>L(Re,z.viewerTopicLabel)),v(j,ue)};I(Se,j=>{z.viewerTopicLabel&&j(_e)})}var kt=m(fe,2),Ft=d(kt),Or=d(Ft),Rr=m(Ft,2);{var Dr=j=>{var ue=dx();v(j,ue)};I(Rr,j=>{var ue;(ue=z.activeWorkspace)!=null&&ue.pinned&&j(Dr)})}var wr=m(Rr,2);{var Yr=j=>{var ue=cx(),Re=d(ue);O(Ge=>L(Re,`Ctrl+${Ge??""}`),[()=>or(z.activeWorkspace)]),v(j,ue)},W=F(()=>or(z.activeWorkspace));I(wr,j=>{r(W)&&j(Yr)})}O(j=>{L(le,z.selectedCompany.corpName),L(me,`${z.selectedCompany.stockCode??""} `),L(Or,`대화: ${j??""}`)},[Er]),v(f,h)},Jd=f=>{var h=fx();v(f,h)};I(Yd,f=>{z.selectedCompany?f(Xd):f(Jd,-1)})}var Qd=m(jn,2),ls=d(Qd),Zd=d(ls);Xo(Zd,{size:13});var ds=m(ls,2),ec=d(ds);Ha(ec,{size:13});var Ls=m(ds,2),tc=d(Ls);{var rc=f=>{gp(f,{size:14})},nc=f=>{bp(f,{size:14})};I(tc,f=>{r(we)?f(rc):f(nc,-1)})}var ac=m(fr,2),oc=d(ac);{var sc=f=>{Yh(f,{get stockCode(){return z.selectedCompany.stockCode},onTopicChange:(h,P)=>z.setViewerTopic(h,P)})},ic=f=>{var h=mx(),P=d(h),le=d(P),fe=d(le);Xn(fe,{size:28,strokeWidth:1.4});var me=m(le,6),Se=d(me);xi(Se,{large:!0,placeholder:"종목명 또는 질문을 입력하세요...",onSend:Mt,onCompanySelect:nr,get inputText(){return r(n)},set inputText(Ft){c(n,Ft,!0)}});var _e=m(me,2);{var kt=Ft=>{var Or=px();ze(Or,21,()=>z.recentCompanies.slice(0,4),Ae,(Rr,Dr)=>{var wr=vx(),Yr=d(wr);O(()=>L(Yr,r(Dr).corpName)),Q("click",wr,()=>nr(r(Dr))),v(Rr,wr)}),v(Ft,Or)};I(_e,Ft=>{z.recentCompanies.length>0&&Ft(kt)})}v(f,h)};I(oc,f=>{z.selectedCompany?f(sc):f(ic,-1)})}var Li=m(Ht,2);{var lc=f=>{var h=hx();Q("click",h,Je),v(f,h)};I(Li,f=>{r(oe)&&r(we)&&f(lc)})}var dc=m(Li,2);{var cc=f=>{var h=bx(),P=d(h),le=d(P),fe=d(le),me=d(fe),Se=d(me);Xo(Se,{size:13});var _e=m(me,2),kt=d(_e);Ha(kt,{size:13});var Ft=m(fe,2),Or=d(Ft);Go(Or,{size:14});var Rr=m(le,2),Dr=d(Rr);{var wr=W=>{var j=be(),ue=Z(j);{var Re=qt=>{Om(qt,{get messages(){return r(pa)},get isLoading(){return r(a)},get scrollTrigger(){return r(_)},get selectedCompany(){return z.selectedCompany},onSend:Mt,onStop:Dn,onRegenerate:Wa,onExport:Cn,onOpenData:Ut,onOpenEvidence:rr,onCompanySelect:nr,get inputText(){return r(n)},set inputText(Jt){c(n,Jt,!0)}})},Ge=qt=>{var Jt=gx(),kr=d(Jt);Xo(kr,{size:28,strokeWidth:1.3,class:"text-dl-text-dim/50"});var Xr=m(kr,6);{var nn=Qt=>{var Mn=xx();Q("click",Mn,je),v(Qt,Mn)};I(Xr,Qt=>{z.activeWorkspace&&Qt(nn)})}var mn=m(Xr,2),$n=d(mn);xi($n,{placeholder:"질문을 입력하세요...",onSend:Mt,onCompanySelect:nr,get inputText(){return r(n)},set inputText(Qt){c(n,Qt,!0)}}),v(qt,Jt)};I(ue,qt=>{r(ma)?qt(Re):qt(Ge,-1)})}v(W,j)},Yr=W=>{{let j=F(()=>z.activeTab||"explore");DataExplorer(W,{get selectedCompany(){return z.selectedCompany},get recentCompanies(){return z.recentCompanies},get activeTab(){return r(j)},get evidenceMessage(){return r(hr)},get activeEvidenceSection(){return z.activeEvidenceSection},get selectedEvidenceIndex(){return z.selectedEvidenceIndex},onSelectCompany:nr,onChangeTab:ue=>z.setTab(ue),onAskAboutModule:De,onNotify:ae,onClose:Je})}};I(Dr,W=>{r(he)==="chat"?W(wr):W(Yr,-1)})}O((W,j,ue)=>{ke(h,1,W),ke(me,1,j),ke(_e,1,ue)},[()=>vt(pt("flex-shrink-0 border-l border-dl-border/30 bg-dl-bg-card/95 backdrop-blur transition-all duration-300",r(oe)?"fixed inset-x-3 bottom-3 top-16 z-30 rounded-2xl shadow-2xl":"w-[420px]")),()=>vt(pt("inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-[11px] transition-colors",r(he)==="chat"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text")),()=>vt(pt("inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-[11px] transition-colors",r(he)==="data"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text"))]),Q("click",me,qe),Q("click",_e,tr),Q("click",Ft,Je),v(f,h)};I(dc,f=>{r(we)&&f(cc)})}var Oi=m(ot,2);{var uc=f=>{var h=Kx(),P=d(h),le=d(P),fe=d(le),me=m(d(fe),2),Se=d(me);Go(Se,{size:18});var _e=m(le,2),kt=d(_e);ze(kt,21,()=>Object.entries(r(i)),Ae,(W,j)=>{var ue=F(()=>Pl(r(j),2));let Re=()=>r(ue)[0],Ge=()=>r(ue)[1];const qt=F(()=>Re()===r(l)),Jt=F(()=>r(E)===Re()),kr=F(()=>Ge().auth==="api_key"),Xr=F(()=>Ge().auth==="cli"),nn=F(()=>r(C)[Re()]||[]),mn=F(()=>r(S)[Re()]);var $n=Hx(),Qt=d($n),Mn=d(Qt),xa=m(Mn,2),ga=d(xa),Ze=d(ga),Zt=d(Ze),sa=m(Ze,2);{var Po=Gt=>{var qr=_x();v(Gt,qr)};I(sa,Gt=>{r(qt)&&Gt(Po)})}var hc=m(ga,2),xc=d(hc),gc=m(xa,2),bc=d(gc);{var _c=Gt=>{Yo(Gt,{size:16,class:"text-dl-success"})},yc=Gt=>{var qr=yx(),ba=Z(qr);Sl(ba,{size:14,class:"text-amber-400"}),v(Gt,qr)},wc=Gt=>{var qr=wx(),ba=Z(qr);qo(ba,{size:14,class:"text-amber-400"}),v(Gt,qr)},kc=Gt=>{var qr=kx(),ba=Z(qr);kp(ba,{size:14,class:"text-dl-text-dim"}),v(Gt,qr)};I(bc,Gt=>{Ge().available?Gt(_c):r(kr)?Gt(yc,1):r(Xr)&&Re()==="codex"&&r(Oe).installed?Gt(wc,2):r(Xr)&&!Ge().available&&Gt(kc,3)})}var Cc=m(Qt,2);{var Sc=Gt=>{var qr=Gx(),ba=Z(qr);{var $c=Nt=>{var er=Sx(),Cr=d(er),Br=d(Cr),hn=m(Cr,2),jr=d(hn),an=m(jr,2),_a=d(an);{var ya=mt=>{Kn(mt,{size:12,class:"animate-spin"})},on=mt=>{Sl(mt,{size:12})};I(_a,mt=>{r(Y)?mt(ya):mt(on,-1)})}var In=m(hn,2);{var Dt=mt=>{var sn=Cx(),Sr=d(sn);qo(Sr,{size:12}),v(mt,sn)};I(In,mt=>{r(T)==="error"&&mt(Dt)})}O(mt=>{L(Br,Ge().envKey?`환경변수 ${Ge().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),Fr(jr,"placeholder",Re()==="openai"?"sk-...":Re()==="claude"?"sk-ant-...":"API Key"),an.disabled=mt},[()=>!r(R).trim()||r(Y)]),Q("keydown",jr,mt=>{mt.key==="Enter"&&V()}),mo(jr,()=>r(R),mt=>c(R,mt)),Q("click",an,V),v(Nt,er)};I(ba,Nt=>{r(kr)&&!Ge().available&&Nt($c)})}var ji=m(ba,2);{var Mc=Nt=>{var er=Mx(),Cr=d(er),Br=d(Cr);Yo(Br,{size:13,class:"text-dl-success"});var hn=m(Cr,2),jr=d(hn),an=m(jr,2);{var _a=on=>{var In=$x(),Dt=d(In);{var mt=Sr=>{Kn(Sr,{size:10,class:"animate-spin"})},sn=Sr=>{var Wn=$a("변경");v(Sr,Wn)};I(Dt,Sr=>{r(Y)?Sr(mt):Sr(sn,-1)})}O(()=>In.disabled=r(Y)),Q("click",In,V),v(on,In)},ya=F(()=>r(R).trim());I(an,on=>{r(ya)&&on(_a)})}Q("keydown",jr,on=>{on.key==="Enter"&&V()}),mo(jr,()=>r(R),on=>c(R,on)),v(Nt,er)};I(ji,Nt=>{r(kr)&&Ge().available&&Nt(Mc)})}var Wi=m(ji,2);{var Ic=Nt=>{var er=Ix(),Cr=m(d(er),2),Br=d(Cr);bs(Br,{size:14});var hn=m(Br,2);Cl(hn,{size:10,class:"ml-auto"}),v(Nt,er)},Tc=Nt=>{var er=Tx(),Cr=d(er),Br=d(Cr);qo(Br,{size:14}),v(Nt,er)};I(Wi,Nt=>{Re()==="ollama"&&!r(s).installed?Nt(Ic):Re()==="ollama"&&r(s).installed&&!r(s).running&&Nt(Tc,1)})}var Vi=m(Wi,2);{var Ac=Nt=>{var er=Px(),Cr=d(er);{var Br=an=>{var _a=Ex(),ya=Z(_a),on=d(ya),In=m(ya,2),Dt=d(In);{var mt=ln=>{var Vn=Ax();v(ln,Vn)};I(Dt,ln=>{r(Oe).installed||ln(mt)})}var sn=m(Dt,2),Sr=d(sn),Wn=d(Sr),Ba=m(In,2);{var No=ln=>{var Vn=zx(),wa=d(Vn);O(()=>L(wa,r(Oe).loginStatus)),v(ln,Vn)};I(Ba,ln=>{r(Oe).loginStatus&&ln(No)})}var Lo=m(Ba,2),Jr=d(Lo);qo(Jr,{size:12,class:"text-amber-400 flex-shrink-0"}),O(()=>{L(on,r(Oe).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),L(Wn,r(Oe).installed?"1.":"2.")}),v(an,_a)};I(Cr,an=>{Re()==="codex"&&an(Br)})}var hn=m(Cr,2),jr=d(hn);O(()=>L(jr,r(Oe).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),v(Nt,er)};I(Vi,Nt=>{r(Xr)&&!Ge().available&&Nt(Ac)})}var qi=m(Vi,2);{var zc=Nt=>{var er=Nx(),Cr=d(er),Br=d(Cr),hn=d(Br);Yo(hn,{size:13,class:"text-dl-success"});var jr=m(Br,2),an=d(jr);vp(an,{size:11}),Q("click",jr,D),v(Nt,er)};I(qi,Nt=>{Re()==="codex"&&Ge().available&&Nt(zc)})}var Ec=m(qi,2);{var Pc=Nt=>{var er=Fx(),Cr=d(er),Br=m(d(Cr),2);{var hn=Dt=>{Kn(Dt,{size:12,class:"animate-spin text-dl-text-dim"})};I(Br,Dt=>{r(mn)&&Dt(hn)})}var jr=m(Cr,2);{var an=Dt=>{var mt=Lx(),sn=d(mt);Kn(sn,{size:14,class:"animate-spin"}),v(Dt,mt)},_a=Dt=>{var mt=Rx();ze(mt,21,()=>r(nn),Ae,(sn,Sr)=>{var Wn=Ox(),Ba=d(Wn),No=m(Ba);{var Lo=Jr=>{ap(Jr,{size:10,class:"inline ml-1"})};I(No,Jr=>{r(Sr)===r(u)&&r(qt)&&Jr(Lo)})}O(Jr=>{ke(Wn,1,Jr),L(Ba,`${r(Sr)??""} `)},[()=>vt(pt("px-3 py-1.5 rounded-lg text-[11px] border transition-all",r(Sr)===r(u)&&r(qt)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),Q("click",Wn,()=>{Re()!==r(l)&&_t(Re()),zt(r(Sr))}),v(sn,Wn)}),v(Dt,mt)},ya=Dt=>{var mt=Dx();v(Dt,mt)};I(jr,Dt=>{r(mn)&&r(nn).length===0?Dt(an):r(nn).length>0?Dt(_a,1):Dt(ya,-1)})}var on=m(jr,2);{var In=Dt=>{var mt=Bx(),sn=d(mt),Sr=m(d(sn),2),Wn=m(d(Sr));Cl(Wn,{size:9});var Ba=m(sn,2);{var No=Jr=>{var ln=jx(),Vn=d(ln),wa=d(Vn),Oo=d(wa);Kn(Oo,{size:12,class:"animate-spin text-dl-primary-light"});var Os=m(wa,2),cs=m(Vn,2),ia=d(cs),Tn=m(cs,2),Rs=d(Tn);O(()=>{$d(ia,`width: ${r($)??""}%`),L(Rs,r(se))}),Q("click",Os,K),v(Jr,ln)},Lo=Jr=>{var ln=qx(),Vn=Z(ln),wa=d(Vn),Oo=m(wa,2),Os=d(Oo);bs(Os,{size:12});var cs=m(Vn,2);ze(cs,21,()=>Pr,Ae,(ia,Tn)=>{const Rs=F(()=>r(nn).some(fo=>fo===r(Tn).name||fo===r(Tn).name.split(":")[0]));var Bi=be(),Nc=Z(Bi);{var Lc=fo=>{var Ds=Vx(),Fi=d(Ds),Gi=d(Fi),Hi=d(Gi),Oc=d(Hi),Ki=m(Hi,2),Rc=d(Ki),Dc=m(Ki,2);{var jc=js=>{var Yi=Wx(),Gc=d(Yi);O(()=>L(Gc,r(Tn).tag)),v(js,Yi)};I(Dc,js=>{r(Tn).tag&&js(jc)})}var Wc=m(Gi,2),Vc=d(Wc),qc=m(Fi,2),Ui=d(qc),Bc=d(Ui),Fc=m(Ui,2);bs(Fc,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),O(()=>{L(Oc,r(Tn).name),L(Rc,r(Tn).size),L(Vc,r(Tn).desc),L(Bc,`${r(Tn).gb??""} GB`)}),Q("click",Ds,()=>{c(H,r(Tn).name,!0),J()}),v(fo,Ds)};I(Nc,fo=>{r(Rs)||fo(Lc)})}v(ia,Bi)}),O(ia=>Oo.disabled=ia,[()=>!r(H).trim()]),Q("keydown",wa,ia=>{ia.key==="Enter"&&J()}),mo(wa,()=>r(H),ia=>c(H,ia)),Q("click",Oo,J),v(Jr,ln)};I(Ba,Jr=>{r(ve)?Jr(No):Jr(Lo,-1)})}v(Dt,mt)};I(on,Dt=>{Re()==="ollama"&&Dt(In)})}v(Nt,er)};I(Ec,Nt=>{(Ge().available||r(kr)||r(Xr))&&Nt(Pc)})}v(Gt,qr)};I(Cc,Gt=>{(r(Jt)||r(qt))&&Gt(Sc)})}O((Gt,qr)=>{ke($n,1,Gt),ke(Mn,1,qr),L(Zt,Ge().label||Re()),L(xc,Ge().desc||"")},[()=>vt(pt("rounded-xl border transition-all",r(qt)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>vt(pt("w-2.5 h-2.5 rounded-full flex-shrink-0",Ge().available?"bg-dl-success":r(kr)?"bg-amber-400":"bg-dl-text-dim"))]),Q("click",Qt,()=>{Ge().available||r(kr)?Re()===r(l)?b(Re()):_t(Re()):b(Re())}),v(W,$n)});var Ft=m(_e,2),Or=d(Ft),Rr=d(Or);{var Dr=W=>{var j=$a();O(()=>{var ue;return L(j,`현재: ${(((ue=r(i)[r(l)])==null?void 0:ue.label)||r(l))??""} / ${r(u)??""}`)}),v(W,j)},wr=W=>{var j=$a();O(()=>{var ue;return L(j,`현재: ${(((ue=r(i)[r(l)])==null?void 0:ue.label)||r(l))??""}`)}),v(W,j)};I(Rr,W=>{r(l)&&r(u)?W(Dr):r(l)&&W(wr,1)})}var Yr=m(Or,2);za(P,W=>c(ce,W),()=>r(ce)),Q("click",h,W=>{W.target===W.currentTarget&&c(w,!1)}),Q("click",me,()=>c(w,!1)),Q("click",Yr,()=>c(w,!1)),v(f,h)};I(Oi,f=>{r(w)&&f(uc)})}var Ri=m(Oi,2);{var fc=f=>{var h=Ux(),P=d(h),le=m(d(P),4),fe=d(le),me=m(fe,2);za(P,Se=>c(re,Se),()=>r(re)),Q("click",h,Se=>{Se.target===Se.currentTarget&&c(M,null)}),Q("click",fe,()=>c(M,null)),Q("click",me,ar),v(f,h)};I(Ri,f=>{r(M)&&f(fc)})}var Di=m(Ri,2);{var vc=f=>{const h=F(()=>z.recentCompanies||[]);var P=tg(),le=d(P),fe=d(le),me=d(fe);Jo(me,{size:18,class:"text-dl-text-dim flex-shrink-0"});var Se=m(me,2);za(Se,W=>c(N,W),()=>r(N));var _e=m(fe,2),kt=d(_e);{var Ft=W=>{var j=Xx(),ue=m(Z(j),2);ze(ue,17,()=>r(X),Ae,(Re,Ge,qt)=>{var Jt=Yx(),kr=d(Jt),Xr=d(kr),nn=m(kr,2),mn=d(nn),$n=d(mn),Qt=m(mn,2),Mn=d(Qt),xa=m(nn,2),ga=m(d(xa),2);Xn(ga,{size:14,class:"text-dl-text-dim"}),O((Ze,Zt)=>{ke(Jt,1,Ze),L(Xr,Zt),L($n,r(Ge).corpName),L(Mn,`${r(Ge).stockCode??""} · ${(r(Ge).market||"")??""}${r(Ge).sector?` · ${r(Ge).sector}`:""}`)},[()=>vt(pt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",qt===r(et)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(Ge).corpName||"?").charAt(0)]),Q("click",Jt,()=>{c(ct,!1),c(Ce,""),c(X,[],!0),c(et,-1),nr(r(Ge))}),qn("mouseenter",Jt,()=>{c(et,qt,!0)}),v(Re,Jt)}),v(W,j)},Or=W=>{var j=Qx(),ue=m(Z(j),2);ze(ue,17,()=>r(h),Ae,(Re,Ge,qt)=>{var Jt=Jx(),kr=d(Jt),Xr=d(kr),nn=m(kr,2),mn=d(nn),$n=d(mn),Qt=m(mn,2),Mn=d(Qt);O((xa,ga)=>{ke(Jt,1,xa),L(Xr,ga),L($n,r(Ge).corpName),L(Mn,`${r(Ge).stockCode??""} · ${(r(Ge).market||"")??""}`)},[()=>vt(pt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",qt===r(et)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(r(Ge).corpName||"?").charAt(0)]),Q("click",Jt,()=>{c(ct,!1),c(Ce,""),c(et,-1),nr(r(Ge))}),qn("mouseenter",Jt,()=>{c(et,qt,!0)}),v(Re,Jt)}),v(W,j)},Rr=F(()=>r(Ce).trim().length===0&&r(h).length>0),Dr=W=>{var j=Zx();v(W,j)},wr=F(()=>r(Ce).trim().length>0),Yr=W=>{var j=eg(),ue=d(j);Jo(ue,{size:24,class:"mb-2 opacity-40"}),v(W,j)};I(kt,W=>{r(X).length>0?W(Ft):r(Rr)?W(Or,1):r(wr)?W(Dr,2):W(Yr,-1)})}Q("click",P,W=>{W.target===W.currentTarget&&c(ct,!1)}),Q("input",Se,()=>{At&&clearTimeout(At),r(Ce).trim().length>=1?At=setTimeout(async()=>{var W;try{const j=await zd(r(Ce).trim());c(X,((W=j.results)==null?void 0:W.slice(0,8))||[],!0)}catch{c(X,[],!0)}},250):c(X,[],!0)}),Q("keydown",Se,W=>{const j=r(X).length>0?r(X):r(h);if(W.key==="ArrowDown")W.preventDefault(),c(et,Math.min(r(et)+1,j.length-1),!0);else if(W.key==="ArrowUp")W.preventDefault(),c(et,Math.max(r(et)-1,-1),!0);else if(W.key==="Enter"&&r(et)>=0&&j[r(et)]){W.preventDefault();const ue=j[r(et)];c(ct,!1),c(Ce,""),c(X,[],!0),c(et,-1),nr(ue)}else W.key==="Escape"&&c(ct,!1)}),mo(Se,()=>r(Ce),W=>c(Ce,W)),v(f,P)};I(Di,f=>{r(ct)&&f(vc)})}var pc=m(Di,2);{var mc=f=>{var h=rg(),P=d(h),le=d(P),fe=d(le),me=m(le,2),Se=d(me);Go(Se,{size:14}),O(_e=>{ke(P,1,_e),L(fe,r(B))},[()=>vt(pt("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",r(pe)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":r(pe)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),Q("click",me,()=>{c(U,!1)}),v(f,h)};I(pc,f=>{r(U)&&f(mc)})}O((f,h,P)=>{ke(st,1,vt(r(oe)?r(x)?"sidebar-mobile":"hidden":"")),ke(uo,1,f),ke(ls,1,h),ke(ds,1,P),Fr(Ls,"title",r(we)?"우측 패널 닫기":"우측 패널 열기")},[()=>vt(pt("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",r(y)?"text-dl-text-dim":r(Va)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5")),()=>vt(pt("inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] transition-colors",r(he)==="chat"&&r(we)?"bg-dl-primary/15 text-dl-primary-light":"text-dl-text-dim hover:bg-white/5 hover:text-dl-text")),()=>vt(pt("inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] transition-colors",r(he)==="data"&&r(we)?"bg-dl-primary/15 text-dl-primary-light":"text-dl-text-dim hover:bg-white/5 hover:text-dl-text"))]),Q("click",tt,Ve),Q("click",Kr,jt),Q("click",uo,()=>ut()),Q("click",Vt,jt),Q("click",ur,()=>Be(-280)),Q("click",Bt,()=>Be(280)),Q("click",ls,qe),Q("click",ds,tr),Q("click",Ls,()=>{r(we)?Je():qe()}),v(e,Hr),ra()}lo(["click","keydown","input"]);yf(ag,{target:document.getElementById("app")});
